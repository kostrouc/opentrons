"""finding coords"""
import sys
from typing import List
import argparse
import asyncio
from opentrons import protocol_api
from hardware_testing.drivers import asair_sensor
from hardware_testing.gravimetric import helpers, workarounds
from opentrons.protocol_engine.types import LabwareOffset
import datetime
import requests
import time
from opentrons.types import Mount
from opentrons.types import Point


from hardware_testing.gravimetric.workarounds import (
    get_sync_hw_api,
)

requirements = {
    "robotType": "OT3",
    "apiLevel": "2.18",
}

LABWARE_OFFSETS: List[LabwareOffset] = []
ip = "10.14.19.236"
print("1")


async def _main(simulate: bool, tiprack: str, removal: int):
    print("6")
    # main()

    # The part where we get and input sensor data.


    LABWARE_OFFSETS.extend(workarounds.http_get_all_labware_offsets())
    print(f"simulate {simulate}")
    protocol = helpers.get_api_context(
        "2.18",  # type: ignore[attr-defined]
        is_simulating=simulate,
        pipette_left="p1000_96",
    )
    for offset in LABWARE_OFFSETS:
        engine = protocol._core._engine_client._transport._engine  # type: ignore[attr-defined]
        if offset.id not in engine.state_view._labware_store._state.labware_offsets_by_id:
            engine.state_view._labware_store._add_labware_offset(offset)
        else:
            print(f"Labware offset ID {offset.id} already exists.")

    hw_api = get_sync_hw_api(protocol)
    for i in range(25):
        hw_api.cache_instruments(require={Mount.LEFT: "p1000_96"})
        attached = hw_api.attached_pipettes
        try:
            print(attached[Mount.LEFT])
            print(attached[Mount.LEFT]['name'])

            break
        except:
            print("failed to find")
            await asyncio.sleep(1)
    run(protocol, tiprack, removal)

# from datetime we get our runtime

def run(protocol: protocol_api.ProtocolContext, tiprack: str, removal: int) -> None:

    print("7")

    # Instrument setup
    pleft = protocol.load_instrument("flex_96channel_1000", "left")
    print("8")
    # DECK SETUP AND LABWARE
    tiprack_1 = protocol.load_labware(tiprack, location="D1")
    pcr_plate = protocol.load_labware(
        "opentrons_96_wellplate_200ul_pcr_full_skirt", location="B3"
    )
    trash_bin = protocol.load_trash_bin("A3")
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", location="D3")
    # tip rack columns
    tiprack_columns = [
        "A1",
        "A2",
        "A3",
        "A4",
        "A5",
        "A6",
        "A7",
        "A8",
        "A9",
        "A10",
        "A11",
        "A12",
    ]
    print("9")
    protocol.home()
    pleft.home()
    hw_api = get_sync_hw_api(protocol)
    print("10")
    
    hw_api.move_to(Mount.LEFT, Point(334,26,250))
    input("Press Enter to continue...")    

    for i in list(range(100)):
        #Center chute for 96ch 50 and 200: 334,26,128, 150 for 1000uL
        hw_api.move_to(Mount.LEFT, Point(334,26,150))
        print(i)
        time.sleep(2)
    protocol.home()
    pleft.home()


    # TODO:
    # connect to google sheet
    # get initial temp/humidity
    # pick up tips
    # aspirate from 12 well
    # dispense into PCR
    # eject tips into trash
    # attempt removal solution
    # repeat for next column

    # get final temp/humidity
    # report software/firmware, pipette serial, robot serial, Pipette type, tip size, total run time from time library


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--tip_type", type=int)
    parser.add_argument("--removal", type=int)
    args = parser.parse_args()
    if args.tip_type == 50:
        tiprack = "opentrons_flex_96_tiprack_50ul"

    if args.tip_type == 200:
        tiprack = "opentrons_flex_96_tiprack_200ul"

    if args.tip_type == 1000:
        tiprack = "opentrons_flex_96_tiprack_1000ul"

    asyncio.run(_main(args.simulate, tiprack, args.removal))

    """testing things bc they dont work
import sys
from typing import List
import argparse
import asyncio
from opentrons import protocol_api
from hardware_testing.drivers import asair_sensor
from hardware_testing.gravimetric import helpers, workarounds
from hardware_testing.opentrons_api import helpers_ot3
from opentrons.protocol_engine.types import LabwareOffset
import datetime
import requests
import time
from opentrons.types import Mount
from opentrons.types import Point


from hardware_testing.gravimetric.workarounds import (
    get_sync_hw_api,
)

requirements = {
    "robotType": "OT3",
    "apiLevel": "2.18",
}

LABWARE_OFFSETS: List[LabwareOffset] = []
ip = "10.14.19.236"
print("1")


async def _main(simulate: bool, tiprack: str, removal: int):
    print("3")
    if not simulate:
        
        # from instruments we get pipette serial
        response = requests.get(
            f"http://{ip}:31950/pipettes", headers={"opentrons-version": "3"}
        )
        pipette_data = response.json()
        pipette_serial = pipette_data['right'].get("id", "")
        print("15")
        print(pipette_serial)


        LABWARE_OFFSETS.extend(workarounds.http_get_all_labware_offsets())
    print(f"simulate {simulate}")
    protocol = helpers.get_api_context(
        "2.18",  # type: ignore[attr-defined]
        is_simulating=simulate,
        pipette_right="p1000_multi_flex",
    )
   
    for offset in LABWARE_OFFSETS:
        engine = protocol._core._engine_client._transport._engine  # type: ignore[attr-defined]
        if offset.id not in engine.state_view._labware_store._state.labware_offsets_by_id:
            engine.state_view._labware_store._add_labware_offset(offset)
        else:
            print(f"Labware offset ID {offset.id} already exists.")

    hw_api = get_sync_hw_api(protocol)
    helpers_ot3.restart_server_ot3()
    for i in range(25):
        hw_api.cache_instruments(require={Mount.RIGHT: "p1000_multi_flex"})
        attached = hw_api.attached_pipettes
        try:
            print(attached[Mount.RIGHT])
            print(attached[Mount.RIGHT]['name'])

            break
        except:
            print("failed to find")
            await asyncio.sleep(2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", action="store_false")
    parser.add_argument("--tip_type", type=int)
    parser.add_argument("--removal", type=int)
    args = parser.parse_args()
    if args.tip_type == 50:
        tiprack = "opentrons_flex_96_tiprack_50ul"

    if args.tip_type == 200:
        tiprack = "opentrons_flex_96_tiprack_200ul"

    if args.tip_type == 1000:
        tiprack = "opentrons_flex_96_tiprack_1000ul"

    asyncio.run(_main(args.simulate, tiprack, args.removal))"""