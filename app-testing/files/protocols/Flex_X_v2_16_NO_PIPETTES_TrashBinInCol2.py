from opentrons import protocol_api

metadata = {
    "protocolName": "QA Protocol - Analysis Error - Trash Bin in Column 2",
    "author": "Derek Maggio <derek.maggio@opentrons.com>",
}

requirements = {
    "robotType": "OT-3",
    "apiLevel": "2.16",
}


def run(ctx: protocol_api.ProtocolContext) -> None:
    ctx.load_trash_bin("C2")
