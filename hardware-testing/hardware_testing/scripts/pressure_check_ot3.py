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

DEFAULT_STABLIZE_TIMEOUT = 60 * 5
DEFAULT_SUBMERGE_MM = -1.5  # aspirate depth below meniscus


@dataclass
class PressureReading:
    sensor_id: SensorId
    pascals: float
    timestamp: float

    def __str__(self) -> str:
        return f"{round(self.pascals, 1)}"


async def _main(is_simulating: bool, submerge: float, offset_tip_rack: Point, offset_reservoir: Point) -> None:
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

    def _flow_rate_all(_fr: float) -> None:
        api.set_flow_rate(mount, aspirate=_fr, dispense=_fr, blow_out=_fr)

    async def _read_pressure() -> Dict[SensorId, PressureReading]:
        nonlocal print_timestamp
        ret: Dict[SensorId, PressureReading] = {}
        for sid in sensor_ids:
            pascals = await helpers_ot3.get_pressure_ot3(api, mount, sid)
            ret[sid] = PressureReading(
                pascals=pascals,
                sensor_id=sid,
                timestamp=time()
            )
        if not print_timestamp or time() - print_timestamp > 0.5:
            print(" , ".join([str(round(p.pascals, 1)) for p in ret.values()]))
            print_timestamp = time()
        return ret

    async def _wait_for_stable_pressure(
            stable_time: float = 1.0, stable_pa: float = 1.0, timeout: float = DEFAULT_STABLIZE_TIMEOUT
    ) -> None:
        data: Dict[SensorId, List[PressureReading]] = {sid: [] for sid in sensor_ids}
        start_time = time()
        duration = 0.0
        while duration < timeout:
            duration = time() - start_time
            pressure = await _read_pressure()
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

    async def _pick_up_tip(name: str, tip: int) -> None:
        await api.retract(mount)
        tip_length = helpers_ot3.get_default_tip_length(tip)
        await helpers_ot3.move_to_arched_ot3(api, mount, _tip_rack(name) + offset_tip_rack)
        await api.pick_up_tip(mount, tip_length=tip_length)
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
                await _read_pressure()
                _flow_rate_all(pip_volume * 0.1)
                try:
                    await api.drop_tip(mount)
                    await _read_pressure()
                    break
                except PipetteOverpressureError as e:
                    print(e)
                    await _read_pressure()
                    print("\ntrying again in a few seconds (or just pull the tip off...)")
                    await api.home(list(types.Axis.gantry_axes()))
                    await helpers_ot3.move_to_arched_ot3(api, mount, loc)
                    for i in range(10, 0, -1):
                        await _read_pressure()
                        await asyncio.sleep(1)
            print("homing plunger, then resuming test")
            await api.home_plunger(mount)
        else:
            await api.drop_tip(mount)
        await api.retract(mount)

    async def _move_to_meniscus() -> None:
        nonlocal well_top_to_meniscus_mm
        await api.retract(mount)
        # offset Y axis in 12-row reservoir
        # also include submerge depth (below top of labware)
        loc = reservoir_a1 + pipette_center_offset._replace(z=well_top_to_meniscus_mm)
        await helpers_ot3.move_to_arched_ot3(api, mount, loc + offset_reservoir)
        while True:
            if _input("ANY KEY to jog down 1mm, or ENTER to aspirate: ").strip():
                await api.move_rel(mount, Point(z=-1.0))
                well_top_to_meniscus_mm -= 1.0
            else:
                break

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

    # RUN
    print("\n\nLabware Locations:")
    print(f"Trash: {SLOT_TRASH}")
    print(f"12-Well Reservoir: {SLOT_RESERVOIR}")
    print(f"Tip-Rack: {SLOT_TIP_RACK}")
    await api.home([ax for ax in types.Axis.gantry_axes()])
    tip_state = await api.get_tip_presence_status(mount)
    if tip_state == types.TipStateType.PRESENT or api.is_simulator:
        await api.add_tip(mount, helpers_ot3.get_default_tip_length(pip_volume))
        await _drop_tip(after_fail=True)
    await api.home_plunger(mount)
    await _wait_for_stable_pressure()
    while True:
        print("----------")
        tip_volume = _input_number("ENTER tip volume: ")
        await _pick_up_tip("A1", tip=int(tip_volume))
        _input_number(f"ENTER aspirate flow-rate: ")
        await _move_to_meniscus()
        await api.move_rel(mount, Point(z=-abs(submerge)))
        flow_rate_aspirate = _input_number(f"ENTER aspirate flow-rate: ")
        flow_rate_dispense = _input_number(f"ENTER dispense flow-rate: ")
        api.set_flow_rate(
            mount,
            aspirate=flow_rate_aspirate,
            dispense=flow_rate_dispense,
            blow_out=flow_rate_dispense
        )
        try:
            await api.aspirate(mount, volume=_input_number(f"ENTER aspirate volume: "))
            await _wait_for_stable_pressure()
            await api.move_rel(mount, Point(z=abs(well_top_to_meniscus_mm)))
            await api.blow_out(mount)
            await api.retract(mount)
            await _wait_for_stable_pressure()
            _input("press ENTER to drop-tip: ")
            await _drop_tip()
        except PipetteOverpressureError as e:
            print(e)
            await _read_pressure()
            await api.home(list(types.Axis.gantry_axes()))
            await _drop_tip(after_fail=True)
        if api.is_simulator:
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--submerge", type=float, default=DEFAULT_SUBMERGE_MM)
    parser.add_argument("--offset-tip-rack", nargs="+", type=float, default=[0, 0, 0])
    parser.add_argument("--offset-reservoir", nargs="+", type=float, default=[0, 0, 0])
    args = parser.parse_args()
    assert len(args.offset_tip_rack) == 3
    assert len(args.offset_reservoir) == 3
    offset_tip_rack = Point(*args.offset_tip_rack)
    offset_reservoir = Point(*args.offset_reservoir)
    asyncio.run(_main(args.simulate, args.submerge, offset_tip_rack, offset_reservoir))
