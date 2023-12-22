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
    plate = ctx.load_labware("corning_96_wellplate_360ul_flat", "D2")

    #######################
    #       PROBING       #
    #######################

    # find liquid heights
    # these methods will modify the "liquid" instance's volume in that well
    with new_tip(single):
        single.find_liquid(reservoir["A1"])
    with new_tip(single):
        single.find_liquid(plate["A1"])

    # 8ch pipette
    with new_tip(multi):
        multi.find_liquid(plate["A2"], plate["H2"])

    #############################
    #       1CH PIPETTING       #
    #############################

    # API defaults to liquid.top(-2) if liquid, else well.bottom(1)
    with new_tip(single):
        single.aspirate(1, reservoir["A1"])
        single.dispense(1, plate["A1"])

    # relative to liquid "top"
    with new_tip(single):
        single.aspirate(1, reservoir["A1"].liquid)
        single.dispense(1, plate["A1"].liquid)

    # same behavior as above
    with new_tip(single):
        single.aspirate(1, reservoir["A1"].liquid.top(-2))
        single.dispense(1, plate["A1"].liquid.top(-2))

    # relative to liquid "top", but based on liquid after a pipetting action
    # will also default to -2mm below meniscus
    with new_tip(single):
        single.aspirate(1, reservoir["A1"].liquid.with_removal(ul=1))
        single.dispense(1, plate["A1"].liquid.with_addition(ul=1))
