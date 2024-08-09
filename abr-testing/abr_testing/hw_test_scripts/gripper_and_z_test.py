"""Test hardware after error in ABR."""
# Author: Nicholas Shiland <nicholas.shiland@opentrons.com>
import argparse
import asyncio
import datetime
import time
import csv
import requests
import os
import json
from requests.auth import HTTPBasicAuth
from typing import List, Tuple, Any, Dict, Optional
from abr_testing.automation import jira_tool
from opentrons_shared_data.errors.exceptions import (
    StallOrCollisionDetectedError,
    PythonException,
)
from hardware_testing.opentrons_api.types import (
    OT3Mount,
    Axis,
    Point,
)
from hardware_testing.opentrons_api.helpers_ot3 import (
    build_async_ot3_hardware_api,
)

async def _main(
    mount: OT3Mount, mount_name: str, simulate: bool, time_min: int, z_axis: Axis
) -> None:

    # make directory for tests. check if directory exists, make if doesn't.
    BASE_DIRECTORY = "/userfs/data/testing_data/gripper_and_z_test/"
    if not os.path.exists(BASE_DIRECTORY):
        os.makedirs(BASE_DIRECTORY)

    # set limits then grab input distance.
    limit = 150
    if mount_name != "gripper":
        limit = 210
    while True:
        try:
            distance = float(
                input(
                    f"How far would you like the z axis to travel? The range is between 1 and {str(limit)}: "
                )
            )
            if 0 < int(distance) <= limit:
                break
            else:
                print(f"Please choose a value between 1 and {str(limit)}.")
        except ValueError:
            print(f"Please enter a number.")

    # Ask, get, and test Jira ticket link
    want_comment = False
    while True:
        y_or_no = input("Do you want to attach the results to a JIRA Ticket? Y/N: ")
        if y_or_no == "Y" or y_or_no == "y":
            # grab testing teams jira api info from a local file
            storage_directory = "/var/lib/jupyter/notebooks"
            jira_info = os.path.join(storage_directory, "jira_credentials.json")
            # create an dict copying the contents of the testing team jira info
            try:
                jira_keys = json.load(open(jira_info))
                # grab token and email from the dict
                tot_info = jira_keys["information"]
                api_token = tot_info["api_token"]
                email = tot_info["email"]
            except FileNotFoundError:
                raise Exception(
                    f"Please add json file with the testing team jira credentials to: {storage_directory}."
                )
            want_comment = True
            while True:
                issue_key = input("Ticket Key: ")
                url = f"https://opentrons.atlassian.net/rest/api/3/issue/{issue_key}"
                auth = HTTPBasicAuth(email, api_token)

                headers = {"Accept": "application/json"}
                response = requests.request("GET", url, headers=headers, auth=auth)
                if str(response) == "<Response [200]>":
                    break
                else:
                    print("Please input a valid JIRA Key")
            ticket = jira_tool.JiraTicket(url, api_token, email)
            break
        elif y_or_no == "N" or y_or_no == "n":
            want_comment = False
            break
        else:
            print("Please Choose a Valid Option")

    # get and confirm robot IP address
    while True:
        ip = input("Robot IP: ")
        # From health: robot name
        try:
            response = requests.get(
                f"http://{ip}:31950/health", headers={"opentrons-version": "3"}
            )
            # confirm connection of IP
            if str(response) == "<Response [200]>":
                break
            else:
                print("Please input a valid IP address")
        except BaseException:
            print("Please input a valid IP address")

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
    if str(instrument_serial) == "None":
        raise Exception("Please specify a valid mount.")

    print(instrument_serial)
    print(robot_name)

    # Create csv file and add initial line
    current_datetime = datetime.datetime.now()
    time_start = current_datetime.strftime("%m-%d, at %H-%M-%S")

    init_data = [
        [
            f"Robot: {robot_name}",
            f" Mount: {mount_name}",
            f" Distance: {distance}",
            f" Instrument Serial: {instrument_serial}",
        ],
    ]

    file_path = f"{BASE_DIRECTORY}/{robot_name} test on {time_start}"

    with open(file_path, mode="w", newline="") as creating_new_csv_file:
        writer = csv.writer(creating_new_csv_file)
        writer.writerows(init_data)

    # hw api setup
    hw_api = await build_async_ot3_hardware_api(
        is_simulating=simulate, use_defaults=True
    )
    await asyncio.sleep(1)
    await hw_api.cache_instruments()
    timeout_start = time.time()
    timeout = time_min * 60
    count = 0
    errored = False
    # finding home and starting to move

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
            runtime = time.time() - timeout_start
            print(f"time: {runtime}")
            # write count and runtime to csv sheet
            run_data = [
                [f"Cycle: {count}", f" Time: {runtime}"],
            ]
            with open(file_path, "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(run_data)
        await hw_api.home()
    except StallOrCollisionDetectedError:
        errored = True
        error_message = "Stall or Collision"
    except PythonException:
        errored = True
        error_message = "KeyboardInterupt"
    except BaseException as e:
        errored = True
        errorn = type(e).__name__
        print(f"THIS ERROR WAS: {errorn}")
        error_message = str(errorn)
    finally:
        # Grab info and comment on JIRA
        await hw_api.disengage_axes([Axis.X, Axis.Y, Axis.Z, Axis.G])
        await hw_api.clean_up()
        if want_comment == True:
            with open(file_path, newline="") as csvfile:
                csvobj = csv.reader(csvfile, delimiter=",")

                full_list = list(csvobj)
                row_of_interest = full_list[count]
                cropped_cycle = str(row_of_interest).split("'")[1]
                cropped_time = str(row_of_interest).split("'")[3]
                cropped_time = cropped_time[1:]

            if errored == True:
                comment_message = f"This test failed due to {error_message} on {cropped_cycle} and {cropped_time}."
            else:
                comment_message = f"This test successfully completed at {cropped_cycle} and {cropped_time}."

            # use REST to comment on JIRA ticket
            comment_item = ticket.format_jira_comment(comment_message)
            ticket.comment(comment_item, url)

            # post csv file created to jira ticket
            attachment_url = url + "/attachments"
            headers = {"Accept": "application/json", "X-Atlassian-Token": "no-check"}

            response = requests.request(
                "POST",
                attachment_url,
                headers=headers,
                auth=auth,
                files={"file": (file_path, open(file_path, "rb"), "application-type")},
            )


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
    elif args.mount == "gripper":
        mount = OT3Mount.GRIPPER
        mount_name = "gripper"
        z_axis = Axis.Z_G
    else:
        mount = OT3Mount.RIGHT
        mount_name = "right"
        z_axis = Axis.Z_R
    print(f"Mount Testing: {mount}")
    asyncio.run(_main(mount, mount_name, args.simulate, args.time_min, z_axis))


if __name__ == "__main__":
    main()
