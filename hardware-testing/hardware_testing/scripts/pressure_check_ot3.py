"""Pressure-Check OT3."""
import argparse
import asyncio
from time import time

from opentrons_hardware.firmware_bindings.constants import SensorId

from opentrons_shared_data.errors.exceptions import PipetteOverpressureError

from hardware_testing.opentrons_api import types
from hardware_testing.opentrons_api.types import Point
from hardware_testing.opentrons_api import helpers_ot3

SLOT_TIP_RACK = 6
SLOT_RESERVOIR = 3
SLOT_TRASH = 12

TRASH_HEIGHT_MM = 40

DEFAULT_SUBMERGE_MM = -1.5  # aspirate depth below meniscus


async def _main(is_simulating: bool, submerge: float) -> None:
    api = await helpers_ot3.build_async_ot3_hardware_api(
        is_simulating=is_simulating, pipette_left="p1000_single_v3.5"
    )

    well_top_to_meniscus_mm = 0.0
    mount = types.OT3Mount.LEFT
    channels = api.hardware_pipettes[mount.to_mount()].channels.value
    pipette_center_offset = Point(
        x=0 if channels <= 8 else 9 * 11 * 0.5,
        y=9 * min(channels, 8) * 0.5,
        z=0
    )

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

    def _flow_rate(_fr: float) -> None:
        api.set_flow_rate(mount, aspirate=_fr, dispense=_fr, blow_out=_fr)

    async def _wait_for_stable_pressure() -> None:
        sensor_ids = [SensorId.S0]
        if channels > 0:
            sensor_ids.append(SensorId.S1)
        pressure_data = {
            sensor_id: []
            for sensor_id in sensor_ids
        }
        inspect_seconds = 30
        start_time = time()
        while time() - start_time < inspect_seconds:
            for sensor_id in sensor_ids:
                pa = await helpers_ot3.get_pressure_ot3(api, mount, sensor_id)
                pressure_data[sensor_id].append(pa)
            print(
                f"{''.join([str(d[-1]) for d in pressure_data.keys()])}"
            )

    def _tip_rack(name: str) -> Point:
        x = 9 * (int(name[1:]) - 1)
        y = -9 * "ABCDEFGH".index(name[0])
        return tip_rack_a1 + Point(x=x, y=y, z=0)

    async def _pick_up_tip(name: str, tip: int) -> None:
        tip_length = helpers_ot3.get_default_tip_length(tip)
        await helpers_ot3.move_to_arched_ot3(api, mount, _tip_rack(name))
        await api.pick_up_tip(mount, tip_length=tip_length)
        await api.retract(mount)

    async def _drop_tip() -> None:
        # offset both XY axes in trash
        loc = trash_nominal + pipette_center_offset
        await helpers_ot3.move_to_arched_ot3(api, mount, loc)
        await api.drop_tip(mount)
        await api.retract(mount)

    async def _move_to_meniscus() -> None:
        nonlocal well_top_to_meniscus_mm
        # offset Y axis in 12-row reservoir
        # also include submerge depth (below top of labware)
        loc = reservoir_a1 + pipette_center_offset._replace(z=well_top_to_meniscus_mm)
        await helpers_ot3.move_to_arched_ot3(api, mount, loc)
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
    await api.home()
    while True:
        print("----------")
        tip_volume = _input_number("ENTER tip volume: ")
        await _pick_up_tip("A1", tip=int(tip_volume))
        await _move_to_meniscus()
        await api.move_rel(mount, Point(z=-abs(submerge)))
        _flow_rate(_input_number(f"ENTER flow-rate: "))
        try:
            await api.aspirate(mount, volume=_input_number(f"ENTER aspirate volume: "))
            await _wait_for_stable_pressure()
            _input("Dispense: ")
            await api.blow_out(mount)
            _input("Retract: ")
            await api.retract(mount)
            _input("Drop-tip: ")
            await _drop_tip()
        except PipetteOverpressureError as e:
            print(e)
            _input("Retract: ")
            await api.retract(mount)
            print("attempting drop-tip at slow-ish speed")
            _flow_rate(tip_volume * 0.1)
            while True:
                try:
                    _input("Drop-tip:")
                    await api.drop_tip(mount)
                    break
                except PipetteOverpressureError as e:
                    print(e)
                    print("\ntry again (or just pull the tip off...)")
            print("homing plunger, then resuming test")
            await api.home_plunger(mount)
        if api.is_simulator:
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--submerge", type=float, default=DEFAULT_SUBMERGE_MM)
    args = parser.parse_args()
    asyncio.run(_main(args.simulate, args.submerge))
