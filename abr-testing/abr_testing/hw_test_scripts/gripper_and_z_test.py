"""Test hardware after error in ABR."""
# Author: Nicholas Shiland <nicholas.shiland@opentrons.com>
import argparse
import asyncio
import datetime
import time
import csv
from opentrons_shared_data import errors
import requests
import os

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
    
    #make folder for tests
    # check if directory exists, make if doesn't
    #BASE_DIRECTORY = "/users/NicholasShiland/Desktop/gripper_and_z_test/"
    BASE_DIRECTORY = "/userfs/data/testing_data/gripper_and_z_test/"
    if not os.path.exists(BASE_DIRECTORY):
        os.makedirs(BASE_DIRECTORY)

    current_datetime = datetime.datetime.now()

    #grab robot info and pipette info
    ip = input("Robot IP: ")
    # From health: robot name
    response = requests.get(
        f"http://{ip}:31950/health", headers={"opentrons-version": "3"}
    )
    print(response)
    health_data = response.json()
    robot_name = health_data.get("name", "")
    # from pipettes/instruments we get pipette/gripper serial
    if mount_name == "gripper":
        response = requests.get(
            f"http://{ip}:31950/instruments", headers={"opentrons-version": "3"}
        )
        instruments = response.json()
        for item in instruments["data"]:
            if item["mount"] == "extension":
                instrument_serial = item["serialNumber"]
        
    else:
        response = requests.get(
            f"http://{ip}:31950/pipettes", headers={"opentrons-version": "3"}
        )
        pipette_data = response.json()
        instrument_serial = pipette_data[mount_name].get("id", "")

    print(instrument_serial)
    print(robot_name)

    # Create csv file and add initial line
    current_datetime = datetime.datetime.now()
    time_start = current_datetime.strftime("%m-%d, at %H-%M-%S")

    init_data = [
        [f"Robot: {robot_name}", f" Mount: {mount_name}", f" distance: dist", f" Instrument Serial: {instrument_serial}"],
    ]

    file_path = f"{BASE_DIRECTORY}/{robot_name} test on {time_start}"

    with open(file_path, mode="w", newline="") as creating_new_csv_file:
        writer = csv.writer(creating_new_csv_file)
        writer.writerows(init_data)

    input("press enter to continue")

    #hw api setup
    hw_api = await build_async_ot3_hardware_api(
        is_simulating=simulate, use_defaults=True
    )
    await asyncio.sleep(1)
    await hw_api.cache_instruments()
    timeout_start = time.time()
    timeout = time_min * 60
    count = 0

    #finding home and starting to move
    try:
        await hw_api.home()
        await asyncio.sleep(1)
        await hw_api.move_rel(mount, Point(0, 0, -1))
        while time.time() < timeout_start + timeout:
            # while True:
            await hw_api.move_rel(mount, Point(0, 0, (-1 * int(distance))))
            await hw_api.move_rel(mount, Point(0, 0, int(distance)))
            # grab and print time and move count
            count += 1
            print(f"cycle: {count}")
            runtime = time.time()-timeout_start
            print(f"time: {runtime}")
            # write count and runtime to csv sheet
            run_data = [
                [f"Cycle: {count}", f" Time: {runtime}"],
            ]
            with open(file_path, "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(run_data)
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