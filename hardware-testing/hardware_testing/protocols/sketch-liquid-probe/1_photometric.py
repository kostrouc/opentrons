from opentrons.protocol_api import ProtocolContext, InstrumentContext


def new_tip(p: InstrumentContext) -> None:
    p.pick_up_tip()
    yield
    p.drop_tip()


def run(ctx: ProtocolContext) -> None:
    single = ctx.load_instrument("flex_1channel_50ul", "left", tip_racks=[
        ctx.load_labware("opentrons_flex_96_tiprack_50ul", "D3")
    ])
    multi = ctx.load_instrument("flex_8channel_1000ul", "left", tip_racks=[
        ctx.load_labware("opentrons_flex_96_tiprack_200ul", "C3")
    ])
    reservoir = ctx.load_labware("nest_12_reservoir_15ml", "D1")
    plate = ctx.load_labware("corning_96_wellplate_360ul_flat", "D2")

    #############################
    #       SETUP LIQUIDS       #
    #############################

    diluent = ctx.define_liquid("diluent", display_color="blue")
    reservoir["A1"].load_liquid(diluent, volume=12600)
    reservoir["A2"].load_liquid(diluent, volume=12600)

    dye = ctx.define_liquid("dye", display_color="red")
    reservoir["A12"].load_liquid(dye, volume=3000)

    ###########################################
    #       CONFIRM KNOWN LIQUID VOLUME       #
    ###########################################

    # use 8ch to confirm diluent is present
    with new_tip(multi):
        multi.confirm_liquid_volume(reservoir["A1"], tolerance_ul=[-500, 2000])
    with new_tip(multi):
        multi.confirm_liquid_volume(reservoir["A2"], tolerance_ul=[-500, 2000])

    # use 1ch to confirm dye is present
    with new_tip(single):
        single.confirm_liquid_volume(reservoir["A12"], tolerance_ul=[-500, 2000])

    ###########################################
    #       SPREAD DILUENT ACROSS PLATE       #
    ###########################################

    with new_tip(multi):
        for plate_column in range(12):
            src_well = reservoir["A1" if plate_column < 6 else "A2"]
            dst_well = plate[f"A{plate_column + 1}"]
            multi.aspirate(volume=199, location=src_well, z_tracking=-2)  # stay 2mm below meniscus
            multi.dispense(volume=199, location=dst_well.liquid, z_tracking=-2)  # allow liquid as an argument

    #########################################
    #       TRANSFER 1uL TO EACH WELL       #
    #########################################

    for dst_well in plate.wells():
        with new_tip(single):
            src_well = reservoir["A12"]
            src_loc = src_well.liquid.after_aspirate(ul=1).top(-2)  # static aspirate
            dst_loc = dst_well.liquid.after_dispense(ul=1).top(-2)  # static dispense
            single.aspirate(volume=1, location=src_loc)
            single.dispense(volume=1, location=dst_loc)
