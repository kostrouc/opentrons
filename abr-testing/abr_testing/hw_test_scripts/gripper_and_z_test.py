"""Test hardware after error in ABR."""
# Author: Nicholas Shiland <nicholas.shiland@opentrons.com>
import argparse
import asyncio
import datetime
import time
import csv
from opentrons_shared_data import errors
import requests

from hardware_testing.opentrons_api.types import (
    OT3Mount,
    Axis,
    Point,
)
from hardware_testing.opentrons_api.helpers_ot3 import (
    build_async_ot3_hardware_api,
)


async def _main(
    mount: OT3Mount, mount_name: str, simulate: bool, time_min: int, z_axis: Axis, distance: int
) -> None:
    #hw api setup
    hw_api = await build_async_ot3_hardware_api(
        is_simulating=simulate, use_defaults=True
    )
    await asyncio.sleep(1)
    await hw_api.cache_instruments()
    timeout_start = time.time()
    timeout = time_min * 60
    count = 0
    
    #grab robot info and pipette info
    #ip = input("Robot IP: ")


    # Create csv file and add initial line


    #finding home and starting to move
    try:
        await hw_api.home()
        await asyncio.sleep(1)
        await hw_api.set_lights(rails=True)
        try:
            await hw_api.grip(force_newtons=None, stay_engaged=True)
        except errors.exceptions.GripperNotPresentError:
            print("Gripper not attached.")
        while time.time() < timeout_start + timeout:
            # while True:
            print(f"time: {time.time()-timeout_start}")
            await hw_api.move_rel(mount, Point(0, 0, -int(distance)))
            await hw_api.move_to(mount, Point(0, 0, int(distance)))
            count += 1
            print(f"cycle: {count}")
        await hw_api.home()
    except KeyboardInterrupt:
        await hw_api.disengage_axes([Axis.X, Axis.Y, Axis.Z, Axis.G])
    finally:
        await hw_api.disengage_axes([Axis.X, Axis.Y, Axis.Z, Axis.G])
        await hw_api.clean_up()


def main() -> None:
    """Run gripper and zmount move commands using arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--time_min", type=int, default=60)
    parser.add_argument(
        "--mount", type=str, choices=["left", "right", "gripper"], default="left"
    )
    args = parser.parse_args()
    print(args.mount)
    if args.mount == "left":
        mount = OT3Mount.LEFT
        mount_name = "left"
        z_axis = Axis.Z_L
        distance = 115
    elif args.mount == "gripper":
        mount = OT3Mount.GRIPPER
        mount_name = "gripper"
        z_axis = Axis.Z_G
        distance = 190
    else:
        mount = OT3Mount.RIGHT
        mount_name = "right"
        z_axis = Axis.Z_R
        distance = 115
    print(f"Mount Testing: {mount}")
    asyncio.run(_main(mount, mount_name, args.simulate, args.time_min, z_axis, distance))


if __name__ == "__main__":
    main()