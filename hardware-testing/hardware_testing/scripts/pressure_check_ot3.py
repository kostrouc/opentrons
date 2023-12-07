"""Pressure-Check OT3."""
import argparse
import asyncio
from dataclasses import dataclass
from time import time
from typing import Dict, List

from opentrons_hardware.firmware_bindings.constants import SensorId

from opentrons_shared_data.errors.exceptions import PipetteOverpressureError

from hardware_testing.opentrons_api import types
from hardware_testing.opentrons_api.types import Point
from hardware_testing.opentrons_api import helpers_ot3

SLOT_TIP_RACK = 6
SLOT_RESERVOIR = 3
SLOT_TRASH = 12

TRASH_HEIGHT_MM = 40

DEFAULT_STABILIZE_TIMEOUT = 60 * 5
DEFAULT_STABILIZE_PASCALS = 5.0
DEFAULT_STABILIZE_SECONDS = 1.0
DEFAULT_SUBMERGE_MM = -1.5  # aspirate depth below meniscus

FLOW_RATE_SAFE = {
    1: {  # 1ch pipette
        50: {  # P50
            50: 5  # 50ul tip
        },
        1000: {  # P1000
            50: 5,  # 50ul tip
            200: 5,  # 200ul tip
            1000: 5  # 1000ul tip
        }
    },
    8: {  # 8ch pipette
        50: {  # P50
            50: 5  # 50ul tip
        },
        1000: {  # P1000
            50: 5,  # 50ul tip
            200: 5,  # 200ul tip
            1000: 5  # 1000ul tip
        }
    }
}

TEST_ASPIRATE_VOLUME = {
    1: {  # 1ch pipette
        50: {  # P50
            50: [1, 5, 10, 20, 50]  # 50ul tip
        },
        1000: {  # P1000
            50: [5, 10, 20, 50],  # 50ul tip
            200: [5, 20, 100, 200],  # 200ul tip
            1000: [10, 100, 500, 1000]  # 1000ul tip
        }
    },
    8: {  # 8ch pipette
        50: {  # P50
            50: [1, 5, 10, 20, 50]  # 50ul tip
        },
        1000: {  # P1000
            50: [5, 10, 20, 50],  # 50ul tip
            200: [5, 20, 100, 200],  # 200ul tip
            1000: [10, 100, 500, 1000]  # 1000ul tip
        }
    }
}

TEST_FLOW_RATE_ASPIRATE = {
    1: {  # 1ch pipette
        50: {  # P50
            50: []  # 50ul tip
        },
        1000: {  # P1000
            50: [],  # 50ul tip
            200: [],  # 200ul tip
            1000: []  # 1000ul tip
        }
    },
    8: {  # 8ch pipette
        50: {  # P50
            50: []  # 50ul tip
        },
        1000: {  # P1000
            50: [1, 5, 10, 15, 20],  # 50ul tip
            200: [],  # 200ul tip
            1000: []  # 1000ul tip
        }
    }
}

TEST_FLOW_RATE_DISPENSE = {
    1: {  # 1ch pipette
        50: {  # P50
            50: []  # 50ul tip
        },
        1000: {  # P1000
            50: [1, 5, 10, 15, 20],  # 50ul tip
            200: [],  # 200ul tip
            1000: []  # 1000ul tip
        }
    },
    8: {  # 8ch pipette
        50: {  # P50
            50: []  # 50ul tip
        },
        1000: {  # P1000
            50: [],  # 50ul tip
            200: [],  # 200ul tip
            1000: []  # 1000ul tip
        }
    }
}


@dataclass
class PressureReading:
    sensor_id: SensorId
    pascals: float
    timestamp: float

    def __str__(self) -> str:
        return f"{round(self.pascals, 1)}"


@dataclass
class TestSettings:
    channels: int
    pipette: int
    tip: int
    volume: float
    flow_rate_aspirate: float
    flow_rate_dispense: float

    def __str__(self) -> str:
        return f"channels-{self.channels}_" \
               f"pipette-{self.pipette}_" \
               f"tip-{self.tip}_" \
               f"volume-{self.volume}_" \
               f"flow-rate-aspirate-{self.flow_rate_aspirate}_" \
               f"flow-rate-dispense-{self.flow_rate_dispense}"


async def _main(is_simulating: bool, tip: int, submerge: float, offset_tip_rack: Point, offset_reservoir: Point) -> None:
    api = await helpers_ot3.build_async_ot3_hardware_api(
        is_simulating=is_simulating, pipette_left="p1000_single_v3.5"
    )

    well_top_to_meniscus_mm = 0.0
    mount = types.OT3Mount.LEFT
    channels = api.hardware_pipettes[mount.to_mount()].channels.value
    pip_name = api.hardware_pipettes[mount.to_mount()].name
    pip_volume = 1000 if "1000" in pip_name else 50
    sensor_ids = [SensorId.S0] if channels == 1 else [SensorId.S0, SensorId.S1]
    pipette_center_offset = Point(
        x=0 if channels <= 8 else 9 * 11 * 0.5,
        y=9 * min(channels, 8) * 0.5,
        z=0
    )
    print_timestamp = 0.0

    # LABWARE
    tip_rack_a1 = helpers_ot3.get_theoretical_a1_position(
        SLOT_TIP_RACK, f"opentrons_flex_96_tiprack_50ul"  # all volumes are same size
    )
    trash_nominal = helpers_ot3.get_slot_calibration_square_position_ot3(
        SLOT_TRASH
    ) + Point(z=TRASH_HEIGHT_MM)
    reservoir_a1 = helpers_ot3.get_theoretical_a1_position(
        SLOT_RESERVOIR, f"nest_1_reservoir_195ml"
    )
    _available_tips = [
        f"{row}{col}"
        for col in range(1, 13)
        for row in "ABCDEFGH"
    ]

    def _flow_rate_all(_fr: float) -> None:
        api.set_flow_rate(mount, aspirate=_fr, dispense=_fr, blow_out=_fr)

    async def _read_pressure() -> Dict[SensorId, PressureReading]:
        ret: Dict[SensorId, PressureReading] = {}
        for sid in sensor_ids:
            pascals = await helpers_ot3.get_pressure_ot3(api, mount, sid)
            ret[sid] = PressureReading(
                pascals=pascals,
                sensor_id=sid,
                timestamp=time()
            )
        return ret

    async def _wait_for_stable_pressure(
            action: str,
            settings: TestSettings,
            stable_time: float = DEFAULT_STABILIZE_SECONDS,
            stable_pa: float = DEFAULT_STABILIZE_PASCALS,
            timeout: float = DEFAULT_STABILIZE_TIMEOUT,
    ) -> None:
        nonlocal print_timestamp
        data: Dict[SensorId, List[PressureReading]] = {sid: [] for sid in sensor_ids}
        start_time = time()
        duration = 0.0
        while duration < timeout:
            duration = time() - start_time
            pressure = await _read_pressure()
            csv_line = [
                settings.channels,
                settings.pipette,
                settings.tip,
                settings.volume,
                settings.flow_rate_aspirate,
                settings.flow_rate_dispense
            ]
            csv_line += [round(p.pascals, 1) for p in pressure.values()]
            data_line = ",".join([str(d) for d in csv_line])
            if not print_timestamp or time() - print_timestamp > 0.5:
                print(data_line)
                print_timestamp = time()
            stable_count = 0
            for sid, press in pressure.items():
                data[sid].append(press)
                prev_n_seconds = [
                    p.pascals
                    for p in data[sid]
                    if p.timestamp > press.timestamp - stable_time
                ]
                if duration > stable_time and max(prev_n_seconds) - min(prev_n_seconds) <= stable_pa:
                    stable_count += 1
            if stable_count == len(sensor_ids):
                print(f"stable after {time() - start_time} seconds")
                return
        print(f"unable to stabilize after {timeout} seconds")

    def _tip_rack(name: str) -> Point:
        x = 9 * (int(name[1:]) - 1)
        y = -9 * "ABCDEFGH".index(name[0])
        return tip_rack_a1 + Point(x=x, y=y, z=0)

    async def _pick_up_tip(tip_vol: int) -> None:
        nonlocal _available_tips
        assert len(_available_tips), "ran out of tip"
        await api.retract(mount)
        tip_length = helpers_ot3.get_default_tip_length(tip_vol)
        tip_pos = _tip_rack(_available_tips[0])
        await helpers_ot3.move_to_arched_ot3(
            api, mount, tip_pos + offset_tip_rack
        )
        await api.pick_up_tip(mount, tip_length=tip_length)
        if not api.is_simulator:
            tip_state = await api.get_tip_presence_status(mount)
            assert tip_state == types.TipStateType.PRESENT, "tip not detected"
        for _ in range(channels):
            _available_tips.pop(0)
        await api.retract(mount)

    async def _drop_tip(after_fail: bool = False) -> None:
        await api.retract(mount)
        # offset both XY axes in trash
        loc = trash_nominal + pipette_center_offset
        await helpers_ot3.move_to_arched_ot3(api, mount, loc)
        if after_fail:
            attempt_count = 0
            while True:
                attempt_count += 1
                print(f"dropping tip slowly (#{attempt_count})")
                _flow_rate_all(FLOW_RATE_SAFE[channels][pip_volume][tip])
                try:
                    await api.drop_tip(mount)
                    tip_state = await api.get_tip_presence_status(mount)
                    assert tip_state == types.TipStateType.ABSENT, "tip still detected"
                    break
                except PipetteOverpressureError as e:
                    print(e)
                    print(await _read_pressure())
                    print("\ntrying again (or just pull the tip off...)")
                    await api.home(list(types.Axis.gantry_axes()))
                    await helpers_ot3.move_to_arched_ot3(api, mount, loc)
            await api.home_plunger(mount)
        else:
            await api.drop_tip(mount)
            tip_state = await api.get_tip_presence_status(mount)
            assert tip_state == types.TipStateType.ABSENT, "tip still detected"
        await api.retract(mount)

    async def _move_to_meniscus() -> None:
        nonlocal well_top_to_meniscus_mm
        await api.retract(mount)
        # offset Y axis in 12-row reservoir
        # also include submerge depth (below top of labware)
        loc = reservoir_a1 + pipette_center_offset._replace(z=well_top_to_meniscus_mm)
        await helpers_ot3.move_to_arched_ot3(api, mount, loc + offset_reservoir)
        if not well_top_to_meniscus_mm:
            while True:
                _inp = _input("\"J\" to jog down 1mm, or \"stop\" at meniscus: ").strip()
                if _inp.lower() == "j":
                    await api.move_rel(mount, Point(z=-1.0))
                    well_top_to_meniscus_mm -= 1.0
                elif _inp.lower() == "stop" or api.is_simulator:
                    break
                else:
                    continue

    def _input(msg: str) -> str:
        if api.is_simulator:
            print(msg)
            return ""
        return input(msg)

    def _input_number(msg: str) -> float:
        if api.is_simulator:
            print(msg + "50")
            return 50
        try:
            return float(_input(msg))
        except ValueError:
            return _input_number(msg)

    async def _test_settings(settings: TestSettings) -> None:
        print("\n\n\n\n----------")
        await _pick_up_tip(tip_vol=int(tip))
        await _wait_for_stable_pressure(action="pick-up-tip", settings=settings)
        await _move_to_meniscus()
        await api.move_rel(mount, Point(z=-abs(submerge)))
        api.set_flow_rate(
            mount,
            aspirate=settings.flow_rate_aspirate,
            dispense=settings.flow_rate_dispense,
            blow_out=settings.flow_rate_dispense
        )
        try:
            await api.aspirate(mount, volume=settings.volume)
            await _wait_for_stable_pressure(action="aspirate", settings=settings)
            await api.move_rel(mount, Point(z=abs(well_top_to_meniscus_mm)))
            await api.blow_out(mount)
            await _wait_for_stable_pressure(action="dispense", settings=settings)
            await api.retract(mount)
            await _drop_tip()
            await _wait_for_stable_pressure(action="drop-tip", settings=settings)
        except PipetteOverpressureError as e:
            print(e)
            print(await _read_pressure())
            await api.home(list(types.Axis.gantry_axes()))
            await _drop_tip(after_fail=True)

    async def _reset_pipette() -> None:
        tip_state = await api.get_tip_presence_status(mount)
        if tip_state == types.TipStateType.PRESENT or api.is_simulator:
            await api.add_tip(mount, helpers_ot3.get_default_tip_length(tip))
            await _drop_tip(after_fail=True)
        await api.home_plunger(mount)
        await _wait_for_stable_pressure(action="drop-tip", settings=_build_default_test_settings())

    def _build_default_test_settings() -> TestSettings:
        return TestSettings(
            channels=channels,
            pipette=pip_volume,
            tip=tip,
            volume=0,
            flow_rate_aspirate=FLOW_RATE_SAFE[channels][pip_volume][tip],
            flow_rate_dispense=FLOW_RATE_SAFE[channels][pip_volume][tip]
        )

    print("\n\nLabware Locations:")
    print(f"Trash: {SLOT_TRASH}")
    print(f"12-Well Reservoir: {SLOT_RESERVOIR}")
    print(f"Tip-Rack: {SLOT_TIP_RACK}")
    await api.home([ax for ax in types.Axis.gantry_axes()])
    await _reset_pipette()
    flow_rates_aspirate = TEST_FLOW_RATE_ASPIRATE[channels][pip_volume][tip]
    flow_rates_dispense = TEST_FLOW_RATE_DISPENSE[channels][pip_volume][tip]
    aspirate_volumes = TEST_ASPIRATE_VOLUME[channels][pip_volume][tip]

    # test aspirate flow-rates
    settings_aspirate = _build_default_test_settings()
    for flow_rate in flow_rates_aspirate:
        settings_aspirate.flow_rate_aspirate = flow_rate
        for volume in aspirate_volumes:
            settings_aspirate.volume = volume
            await _test_settings(settings_aspirate)

    # test dispense flow-rates
    settings_dispense = _build_default_test_settings()
    for flow_rate in flow_rates_dispense:
        settings_dispense.flow_rate_dispense = flow_rate
        for volume in aspirate_volumes:
            settings_dispense.volume = volume
            await _test_settings(settings_dispense)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--tip", type=int, required=True)
    parser.add_argument("--submerge", type=float, default=DEFAULT_SUBMERGE_MM)
    parser.add_argument("--offset-tip-rack", nargs="+", type=float, default=[0, 0, 0])
    parser.add_argument("--offset-reservoir", nargs="+", type=float, default=[0, 0, 0])
    args = parser.parse_args()
    assert len(args.offset_tip_rack) == 3
    assert len(args.offset_reservoir) == 3
    asyncio.run(_main(
        args.simulate,
        args.tip,
        args.submerge,
        Point(*args.offset_tip_rack),
        Point(*args.offset_reservoir)
    ))
