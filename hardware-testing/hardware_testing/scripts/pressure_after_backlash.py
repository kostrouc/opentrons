"""Pressure after backlash."""
import argparse
import asyncio
from time import time

from opentrons_hardware.firmware_bindings.constants import SensorId

from hardware_testing.opentrons_api.types import OT3Mount, Point, OT3AxisKind
from hardware_testing.opentrons_api import helpers_ot3


READ_INTERVAL_SECONDS = 0.5
HOVER_MM = 3.0


async def _main(is_simulating: bool) -> None:
    mount = OT3Mount.LEFT
    api = await helpers_ot3.build_async_ot3_hardware_api(is_simulating=is_simulating, pipette_left="p1000_96_v3.4")
    await api.home()

    print("jog to pick-up-tip location")
    await helpers_ot3.jog_mount_ot3(api, mount)
    await api.pick_up_tip(mount, helpers_ot3.get_default_tip_length(50))
    await api.retract(mount)
    print("jog to rubber pad")
    await helpers_ot3.jog_mount_ot3(api, mount)

    # NOTE: re-setting the gantry-load will reset the move-manager's per-axis constraints
    api.config.motion_settings.max_speed_discontinuity.high_throughput[
        OT3AxisKind.P
    ] = 0.41
    await api.set_gantry_load(api.gantry_load)

    # move up a bit, prepare for aspirate, then move back down
    await api.move_rel(mount, Point(z=HOVER_MM))
    await api.prepare_for_aspirate(mount)
    await api.move_rel(mount, Point(z=-HOVER_MM))

    # NOTE: re-setting the gantry-load will reset the move-manager's per-axis constraints
    api.config.motion_settings.max_speed_discontinuity.high_throughput[
        OT3AxisKind.P
    ] = 5.0
    await api.set_gantry_load(api.gantry_load)

    # read the pressure sensor and print out values and timestamp
    start_time = time()
    while True:
        val_a1 = int(await helpers_ot3.get_pressure_ot3(api, mount, SensorId.S0))
        val_h12 = int(await helpers_ot3.get_pressure_ot3(api, mount, SensorId.S1))
        print(f"[{int(time() - start_time)}] pressure: A1={val_a1}, H12={val_h12}")
        if is_simulating and time() - start_time > 2.0:
            break
        await asyncio.sleep(0.1 if is_simulating else READ_INTERVAL_SECONDS)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", action="store_true")
    args = parser.parse_args()
    asyncio.run(_main(args.simulate))
