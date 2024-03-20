"""DEBUG Photometric OT3 P1000."""
from opentrons.protocol_api import ProtocolContext

metadata = {"protocolName": "DEBUG-photometric-ot3-p1000-96"}
requirements = {"robotType": "Flex", "apiLevel": "2.15"}

TEST_VOLUME = 0.5
ASPIRATE_HEIGHT_FROM_BOTTOM = 1
DISPENSE_HEIGHT_FROM_BOTTOM = 6

PUSH_OUT = 10
FLOW_RATE = {
    "aspirate": 6.5,
    "dispense": 80
}
AIR_GAP = 0.1

SLOTS_TIPRACK = {
    50: [5, 6, 8, 9, 11]
}
SLOT_PLATE = 3
SLOT_RESERVOIR = 2

RESERVOIR_LABWARE = "nest_1_reservoir_195ml"
PHOTOPLATE_LABWARE = "corning_96_wellplate_360ul_flat"


def run(ctx: ProtocolContext) -> None:
    """Run."""
    tipracks = [
        # FIXME: use official tip-racks once available
        ctx.load_labware(
            f"opentrons_flex_96_tiprack_{size}uL_adp", slot, namespace="custom_beta"
        )
        for size, slots in SLOTS_TIPRACK.items()
        for slot in slots
        if size == 50  # only calibrate 50ul tips for 96ch test
    ]
    reservoir = ctx.load_labware(RESERVOIR_LABWARE, SLOT_RESERVOIR)
    plate = ctx.load_labware(PHOTOPLATE_LABWARE, SLOT_PLATE)
    pipette = ctx.load_instrument("flex_96channel_1000", "left")
    pipette.configure_for_volume(TEST_VOLUME)
    pipette.flow_rate.aspirate = FLOW_RATE["aspirate"]
    pipette.flow_rate.dispense = FLOW_RATE["dispense"]

    for rack in tipracks:
        pipette.pick_up_tip(rack["A1"])

        # ASPIRATE
        pipette.aspirate(TEST_VOLUME, reservoir["A1"].bottom(ASPIRATE_HEIGHT_FROM_BOTTOM))
        if AIR_GAP:
            pipette.air_gap(AIR_GAP)
        ctx.delay(seconds=1.0)

        # DISPENSE
        if AIR_GAP:
            pipette.dispense(AIR_GAP, plate["A1"].top(), push_out=PUSH_OUT)
        disp_pos = plate["A1"].bottom(DISPENSE_HEIGHT_FROM_BOTTOM)
        pipette.dispense(pipette.current_volume, disp_pos, push_out=PUSH_OUT)
        ctx.delay(seconds=0.5)
        pipette.touch_tip(speed=30)
        pipette.blow_out()

        pipette.drop_tip()
