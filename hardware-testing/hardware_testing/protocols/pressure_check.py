"""Check by Eye dot Py."""
from opentrons.protocol_api import ProtocolContext
from datetime import datetime

metadata = {"protocolName": "PRESSURE-CHECK-V3"}
requirements = {"robotType": "Flex", "apiLevel": "2.15"}

DEBUG_CHECK_PRESSURE = True

PIP_CHANNELS = 8
PIP_VOLUME = 50
PIP_MOUNT = "left"
PIP_PUSH_OUT = 6

TIP_VOLUME = 50

# NOTE: pipette will loop through volumes
#       circling back to the first, regardless of which well it is at
#       so number of volumes can be any length you like (example: [1])
TEST_VOLUMES = [0.5]
PRE_WET_COUNT = 5

# FIXME: operator must LPC to liquid-surface in reservoir in order for this to work
#        need to get liquid-probing working ASAP to fix this hack
ASPIRATE_DEPTH = -2.0
DISPENSE_DEPTH = -1.5
BLOW_OUT_HEIGHT = 5.0

ASPIRATE_FLOW_RATE = 35  # default for P50S and P50M is 35ul/sec
DISPENSE_FLOW_RATE = 57  # default for P50S and P50M is 57ul/sec

ASPIRATE_PRE_DELAY = 0.25
ASPIRATE_POST_DELAY = 1.0
DISPENSE_PRE_DELAY = 0.0
DISPENSE_POST_DELAY = 0.5

RESERVOIR_SLOT = "D1"
RESERVOIR_NAME = "nest_1_reservoir_195ml"
RESERVOIR_WELL = "A1"

PLATE_NAME = "corning_96_wellplate_360ul_flat"

RACK_AND_PLATE_SLOTS = [  # [rack, plate]
    ["B1", "C1"],
    # ["B2", "C2"],
    # ["B3", "C3"],
    # ["A1", "D2"],
    # ["A2", "D3"],
]

HEIGHT_OF_200UL_IN_PLATE_MM = 6.04  # height of 200ul in a Corning 96-well flat-bottom

# FIXME: get liquid-probe woring in API, then delete this
RESERVOIR_LPC_OFFSET = -10


def run(ctx: ProtocolContext) -> None:
    """Run."""
    pipette = ctx.load_instrument(f"flex_{PIP_CHANNELS}channel_{PIP_VOLUME}", PIP_MOUNT)
    reservoir = ctx.load_labware(RESERVOIR_NAME, RESERVOIR_SLOT)
    if DEBUG_CHECK_PRESSURE and not ctx.is_simulating():
        hw = ctx._core.get_hardware()
        hw.open_pressure_csv(
            f"{metadata['protocolName']}-{datetime.now().strftime('%H-%M-%S')}.csv"
        )
        hw.change_pressure_tag("")

    def _tag_pressure(tag: str) -> None:
        if DEBUG_CHECK_PRESSURE and not ctx.is_simulating():
            hw.change_pressure_tag(tag)

    combos = [
        {
            "rack": ctx.load_labware(
                f"opentrons_flex_96_tiprack_{TIP_VOLUME}uL", pair[0]
            ),
            "plate": ctx.load_labware(PLATE_NAME, pair[1]),
        }
        for pair in RACK_AND_PLATE_SLOTS
    ]

    pipette.flow_rate.aspirate = ASPIRATE_FLOW_RATE
    pipette.flow_rate.dispense = DISPENSE_FLOW_RATE
    vol_cnt = 0
    for combo in combos:
        plate = combo["plate"]
        rack = combo["rack"]
        num_trials = 12 if PIP_CHANNELS == 8 else 96
        for trial in range(num_trials):
            csv_sub_string = f"plate-{plate.parent}-trial{trial + 1}"

            # CHOOSE VOLUME
            volume = TEST_VOLUMES[vol_cnt % len(TEST_VOLUMES)]
            vol_cnt += 1

            # CHOOSE WELL
            column = (trial % 12) + 1
            row = "ABCDEFGH"[int(trial / 12)]
            well_name = f"{row}{column}"

            # CRITICAL POSITIONS
            aspirate_pos = reservoir[RESERVOIR_WELL].top(
                ASPIRATE_DEPTH + RESERVOIR_LPC_OFFSET
            )
            blow_out_pos_pre_wet = reservoir[RESERVOIR_WELL].top(
                BLOW_OUT_HEIGHT + RESERVOIR_LPC_OFFSET
            )
            dispense_pos = plate[well_name].bottom(
                HEIGHT_OF_200UL_IN_PLATE_MM + DISPENSE_DEPTH
            )
            blow_out_pos_dispense = plate[well_name].top()

            # PICK-UP TIP
            pipette.configure_for_volume(volume)
            pipette.pick_up_tip(rack[well_name])

            # PRE-WET
            pipette.move_to(aspirate_pos)
            _tag_pressure(f"pre-wet-{csv_sub_string}")
            ctx.delay(seconds=ASPIRATE_PRE_DELAY)
            for i in range(PRE_WET_COUNT):
                pipette.aspirate(volume, aspirate_pos)
                push_out = 0 if i < PRE_WET_COUNT - 1 else PIP_PUSH_OUT
                pipette.dispense(volume, aspirate_pos, push_out=push_out)
            ctx.delay(seconds=DISPENSE_POST_DELAY)
            pipette.blow_out(blow_out_pos_pre_wet)
            _tag_pressure("")

            # PREPARE-TO-ASPIRATE
            # FIXME: replace with "prepare-for-aspirate" once added to API
            # NOTE: this hack moving 0.0001 ul is guaranteed to not create any
            #       actual movement in the plunger, because it is smaller than
            #       the minimum allowed movement (0.05 mm) set by software
            pipette.aspirate(0.0001, blow_out_pos_pre_wet)
            pipette.dispense(0.0001, blow_out_pos_pre_wet, push_out=0)

            # ASPIRATE
            pipette.move_to(aspirate_pos)
            _tag_pressure(f"aspirate-{csv_sub_string}")
            ctx.delay(seconds=ASPIRATE_PRE_DELAY)
            pipette.aspirate(volume, aspirate_pos)
            ctx.delay(seconds=ASPIRATE_POST_DELAY)
            _tag_pressure("")
            pipette.move_to(blow_out_pos_dispense)

            # DISPENSE
            pipette.move_to(dispense_pos)
            _tag_pressure(f"dispense-{csv_sub_string}")
            ctx.delay(seconds=DISPENSE_PRE_DELAY)
            pipette.dispense(volume, dispense_pos, push_out=PIP_PUSH_OUT)
            ctx.delay(seconds=DISPENSE_POST_DELAY)
            _tag_pressure("")

            # BLOW-OUT
            pipette.move_to(blow_out_pos_dispense)
            _tag_pressure(f"blowout-{csv_sub_string}")
            pipette.blow_out(blow_out_pos_dispense)
            _tag_pressure("")

            # DROP TIP
            pipette.drop_tip(rack[well_name], home_after=False)

    if DEBUG_CHECK_PRESSURE and not ctx.is_simulating():
        hw.close_pressure_csv()
