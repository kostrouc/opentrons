from opentrons.protocol_api import ProtocolContext, InstrumentContext


def new_tip(p: InstrumentContext) -> None:
    p.pick_up_tip()
    yield
    p.drop_tip()


def run(ctx: ProtocolContext) -> None:
    single = ctx.load_instrument("flex_1channel_1000ul", "left", tip_racks=[
        ctx.load_labware("opentrons_flex_96_tiprack_50ul", "D3")
    ])
    multi = ctx.load_instrument("flex_8channel_1000ul", "left", tip_racks=[
        ctx.load_labware("opentrons_flex_96_tiprack_50ul", "C3")
    ])
    reservoir = ctx.load_labware("nest_12_reservoir_15ml", "D1")
    plate = ctx.load_labware("opentrons_96_wellplate_200ul_pcr_full_skirt", "D2")
    tuberack = ctx.load_labware("opentrons_24_tuberack_nest_2ml_screwcap", "C2")

    #############################
    #       SETUP LIQUIDS       #
    #############################

    water = ctx.define_liquid("water", display_color="blue")
    reservoir["A1"].load_liquid(water, volume=7800)

    sample = ctx.define_liquid("sample", display_color="green")
    for tube in tuberack.wells():
        tube.load_liquid(sample, unknown_ul=True)  # NOTE: there is something there, we just don't know how much

    ###########################################
    #       CONFIRM KNOWN LIQUID VOLUME       #
    ###########################################

    # use 8ch to confirm water is present
    with new_tip(multi):
        multi.confirm_liquid_volume(reservoir["A1"], tolerance_ul=[-500, 2000])

    #################################################
    #       SEARCH FOR UNKNOWN LIQUID VOLUMES       #
    #################################################

    # NOTE: there is something there, we just don't know how much
    # NOTE: each volume found will be saved/tracked internally
    for tube in tuberack.wells():
        with new_tip(single):
            single.find_liquid_volume(tube)

    #########################################
    #       SPREAD WATER ACROSS PLATE       #
    #########################################

    with new_tip(multi):
        for plate_column in range(12):
            src_well = reservoir["A1"]
            dst_well = plate[f"A{plate_column + 1}"]
            multi.aspirate(volume=199, location=src_well, z_tracking=-2)
            multi.dispense(volume=199, location=dst_well, z_tracking=-2)

    #########################################
    #       TRANSFER 1uL TO EACH WELL       #
    #########################################

    for dst_well in plate.wells():
        with new_tip(single):
            src_well = reservoir["A12"]
            src_loc = src_well.liquid.after_aspirate(ul=1).top(-2)
            dst_loc = dst_well.liquid.after_dispense(ul=1).top(-2)
            single.aspirate(volume=1, location=src_loc)
            single.dispense(volume=1, location=dst_loc)
