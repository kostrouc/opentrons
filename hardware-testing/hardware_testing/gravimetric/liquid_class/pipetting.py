"""Pipette motions."""
from dataclasses import dataclass
from typing import Optional, Callable, Tuple

from opentrons.config.defaults_ot3 import DEFAULT_MAX_SPEED_DISCONTINUITY
from opentrons.protocol_api import InstrumentContext, ProtocolContext
from opentrons.protocol_api.labware import Well

from hardware_testing.opentrons_api.types import OT3AxisKind
from hardware_testing.gravimetric import config
from hardware_testing.gravimetric.liquid_height.height import LiquidTracker
from hardware_testing.opentrons_api.types import OT3Mount, Point

from .definition import LiquidClassSettings
from .defaults import get_liquid_class


@dataclass
class LiquidSurfaceHeights:
    """Liquid Surface Heights."""

    above: float
    below: float


@dataclass
class PipettingHeights:
    """Pipetting heights."""

    start: LiquidSurfaceHeights
    end: LiquidSurfaceHeights


def _get_heights_in_well(
    height_before: float,
    height_after: float,
    submerge: float,
    retract: float,
) -> Tuple[float, float, float]:
    pipetting_heights = PipettingHeights(
        start=LiquidSurfaceHeights(
            above=max(height_before + retract, config.LABWARE_BOTTOM_CLEARANCE),
            below=max(height_before - submerge, config.LABWARE_BOTTOM_CLEARANCE),
        ),
        end=LiquidSurfaceHeights(
            above=max(height_after + retract, config.LABWARE_BOTTOM_CLEARANCE),
            below=max(height_after - submerge, config.LABWARE_BOTTOM_CLEARANCE),
        ),
    )
    approach = max(pipetting_heights.start.above, pipetting_heights.end.above)
    submerge = pipetting_heights.end.below
    retract = pipetting_heights.end.above
    return approach, submerge, retract


@dataclass
class PipettingCallbacks:
    """Pipetting callbacks."""

    on_submerging: Callable
    on_mixing: Callable
    on_aspirating: Callable
    on_dispensing: Callable
    on_retracting: Callable
    on_blowing_out: Callable
    on_exiting: Callable


def _check_aspirate_dispense_args(
    mix: Optional[float], aspirate: Optional[float], dispense: Optional[float]
) -> None:
    if mix is None and aspirate is None and dispense is None:
        raise ValueError("either mix, aspirate or dispense volume must be set")
    if aspirate and dispense or mix and aspirate or mix and dispense:
        raise ValueError("only a mix, aspirate or dispense volumes can be set")


def _get_approach_submerge_retract_heights(
    well: Well,
    liquid_tracker: LiquidTracker,
    liquid_class: LiquidClassSettings,
    mix: Optional[float],
    aspirate: Optional[float],
    dispense: Optional[float],
    blank: bool,
    channel_count: int,
) -> Tuple[float, float, float]:
    liquid_before, liquid_after = liquid_tracker.get_before_and_after_heights(
        well,
        aspirate=aspirate if aspirate else 0,
        dispense=dispense,
        channels=channel_count,
    )
    if blank:
        # force the pipette to move above the well
        liquid_before = well.depth + (well.depth - liquid_before)
        liquid_after = well.depth + (well.depth - liquid_after)
    if aspirate:
        liq_submerge = liquid_class.aspirate.z_submerge_depth
        liq_retract = liquid_class.aspirate.z_retract_height
    else:
        liq_submerge = liquid_class.dispense.z_submerge_depth
        liq_retract = liquid_class.dispense.z_retract_height
    approach_mm, submerge_mm, retract_mm = _get_heights_in_well(
        liquid_before, liquid_after, liq_submerge, liq_retract
    )
    return approach_mm, submerge_mm, retract_mm


def _submerge(
    pipette: InstrumentContext,
    well: Well,
    height: float,
    channel_offset: Point,
    speed: float,
) -> None:
    pipette.move_to(
        well.bottom(height).move(channel_offset),
        speed=speed,
    )


def _retract(
    ctx: ProtocolContext,
    pipette: InstrumentContext,
    well: Well,
    channel_offset: Point,
    mm_above_well_bottom: float,
    speed: float,
    z_discontinuity: float,
) -> None:
    # change discontinuity per the liquid-class settings
    hw_api = ctx._core.get_hardware()
    if pipette.channels == 96:
        hw_api.config.motion_settings.max_speed_discontinuity.high_throughput[
            OT3AxisKind.Z
        ] = z_discontinuity
    else:
        hw_api.config.motion_settings.max_speed_discontinuity.low_throughput[
            OT3AxisKind.Z
        ] = z_discontinuity
    # NOTE: re-setting the gantry-load will reset the move-manager's per-axis constraints
    hw_api.set_gantry_load(hw_api.gantry_load)
    # retract out of the liquid (not out of the well)
    pipette.move_to(well.bottom(mm_above_well_bottom).move(channel_offset), speed=speed)
    # reset discontinuity back to default
    if pipette.channels == 96:
        hw_api.config.motion_settings.max_speed_discontinuity.high_throughput[
            OT3AxisKind.Z
        ] = DEFAULT_MAX_SPEED_DISCONTINUITY.high_throughput[OT3AxisKind.Z]
    else:
        hw_api.config.motion_settings.max_speed_discontinuity.low_throughput[
            OT3AxisKind.Z
        ] = DEFAULT_MAX_SPEED_DISCONTINUITY.low_throughput[OT3AxisKind.Z]
    # NOTE: re-setting the gantry-load will reset the move-manager's per-axis constraints
    hw_api.set_gantry_load(hw_api.gantry_load)


def _pipette_with_liquid_settings(  # noqa: C901
    ctx: ProtocolContext,
    pipette: InstrumentContext,
    liquid_class: LiquidClassSettings,
    well: Well,
    channel_offset: Point,
    channel_count: int,
    liquid_tracker: LiquidTracker,
    callbacks: PipettingCallbacks,
    mix: Optional[float] = None,
    aspirate: Optional[float] = None,
    dispense: Optional[float] = None,
    blank: bool = True,
    added_blow_out: bool = True,
    touch_tip: bool = False,
) -> None:
    """Run a pipette given some Pipetting Liquid Settings."""
    # FIXME: stop using hwapi, and get those functions into core software
    hw_api = ctx._core.get_hardware()
    hw_mount = OT3Mount.LEFT if pipette.mount == "left" else OT3Mount.RIGHT
    hw_pipette = hw_api.hardware_pipettes[hw_mount.to_mount()]
    _check_aspirate_dispense_args(mix, aspirate, dispense)

    def _dispense_with_added_blow_out() -> None:
        # dispense all liquid, plus some air by calling `pipette.blow_out(location, volume)`
        # FIXME: this is a hack, until there's an equivalent `pipette.blow_out(location, volume)`
        hw_api = ctx._core.get_hardware()
        hw_mount = OT3Mount.LEFT if pipette.mount == "left" else OT3Mount.RIGHT
        hw_api.blow_out(hw_mount, liquid_class.dispense.blow_out_submerged)

    def _blow_out_remaining_air() -> None:
        # FIXME: using the HW-API to specify that we want to blow-out the full
        #        available blow-out volume
        # NOTE: calculated using blow-out distance (mm) and the nominal ul-per-mm
        blow_out_ul_per_mm = hw_pipette.config.shaft_ul_per_mm
        bottom = hw_pipette.plunger_positions.bottom
        blow_out = hw_pipette.plunger_positions.blow_out
        max_blow_out_ul = (blow_out - bottom) * blow_out_ul_per_mm
        hw_api.blow_out(hw_mount, max_blow_out_ul)

    def _set_plunger_bottom() -> None:
        # FIXME: this should be deleted immediately once low-volume mode is working
        old_positions = hw_pipette.plunger_positions
        if (aspirate and aspirate < 5) or (dispense and dispense < 5):
            old_positions.bottom = 61.5
        else:
            old_positions.bottom = 71.5
        hw_pipette._set_plunger_positions(old_positions)

    # ASPIRATE/DISPENSE SEQUENCE HAS THREE PHASES:
    #  1. APPROACH
    #  2. SUBMERGE
    #  3. RETRACT

    # CALCULATE TIP HEIGHTS FOR EACH PHASE
    approach_mm, submerge_mm, retract_mm = _get_approach_submerge_retract_heights(
        well,
        liquid_tracker,
        liquid_class,
        mix,
        aspirate,
        dispense,
        blank,
        channel_count,
    )

    # SET Z SPEEDS DURING SUBMERGE/RETRACT
    if aspirate or mix:
        submerge_speed = config.TIP_SPEED_WHILE_SUBMERGING_ASPIRATE
        retract_speed = config.TIP_SPEED_WHILE_RETRACTING_ASPIRATE
        _z_disc = liquid_class.aspirate.z_retract_discontinuity
    else:
        submerge_speed = config.TIP_SPEED_WHILE_SUBMERGING_DISPENSE
        retract_speed = config.TIP_SPEED_WHILE_RETRACTING_DISPENSE
        _z_disc = liquid_class.dispense.z_retract_discontinuity

    # CREATE CALLBACKS FOR EACH PHASE
    def _aspirate_on_approach() -> None:
        _set_plunger_bottom()
        hw_api.prepare_for_aspirate(hw_mount)
        if liquid_class.aspirate.leading_air_gap > 0:
            pipette.aspirate(liquid_class.aspirate.leading_air_gap)

    def _aspirate_on_mix() -> None:
        callbacks.on_mixing()
        _submerge(pipette, well, submerge_mm, channel_offset, submerge_speed)
        _num_mixes = 5
        for i in range(_num_mixes):
            pipette.aspirate(mix)
            ctx.delay(liquid_class.aspirate.delay)
            if i < _num_mixes - 1:
                pipette.dispense(mix)
            else:
                _dispense_with_added_blow_out()
            ctx.delay(liquid_class.dispense.delay)
        # don't go all the way up to retract position, but instead just above liquid
        _retract(
            ctx, pipette, well, channel_offset, approach_mm, retract_speed, _z_disc
        )
        _blow_out_remaining_air()
        hw_api.prepare_for_aspirate(hw_mount)
        assert pipette.current_volume == 0

    def _aspirate_on_submerge() -> None:
        # aspirate specified volume
        callbacks.on_aspirating()
        pipette.aspirate(aspirate)
        # update liquid-height tracker
        liquid_tracker.update_affected_wells(
            well, aspirate=aspirate, channels=channel_count
        )
        # delay
        ctx.delay(liquid_class.aspirate.delay)

    def _aspirate_on_retract() -> None:
        # add trailing-air-gap
        pipette.aspirate(liquid_class.aspirate.trailing_air_gap)

    def _dispense_on_approach() -> None:
        # remove trailing-air-gap
        pipette.dispense(liquid_class.aspirate.trailing_air_gap)

    def _dispense_on_submerge() -> None:
        callbacks.on_dispensing()
        if added_blow_out:
            _dispense_with_added_blow_out()
        else:
            pipette.dispense(dispense)
        # update liquid-height tracker
        liquid_tracker.update_affected_wells(
            well, dispense=dispense, channels=channel_count
        )
        # delay
        ctx.delay(liquid_class.dispense.delay)

    def _dispense_on_retract() -> None:
        if pipette.current_volume <= 0 and added_blow_out:
            # blow-out any remaining air in pipette (any reason why not?)
            callbacks.on_blowing_out()
            _blow_out_remaining_air()
            hw_api.prepare_for_aspirate(hw_mount)
        if touch_tip:
            pipette.touch_tip(speed=config.TOUCH_TIP_SPEED)
        # NOTE: always do a trailing-air-gap, regardless of if tip is empty or not
        #       to avoid droplets from forming and falling off the tip
        pipette.aspirate(liquid_class.aspirate.trailing_air_gap)

    # PHASE 1: APPROACH
    pipette.flow_rate.aspirate = liquid_class.aspirate.plunger_flow_rate
    pipette.flow_rate.dispense = liquid_class.dispense.plunger_flow_rate
    pipette.flow_rate.blow_out = liquid_class.dispense.plunger_flow_rate
    pipette.move_to(well.bottom(approach_mm).move(channel_offset))
    _aspirate_on_approach() if aspirate or mix else _dispense_on_approach()

    if mix:
        # PHASE 2A: MIXING
        _aspirate_on_mix()
    else:
        # PHASE 2B: ASPIRATE or DISPENSE
        callbacks.on_submerging()
        _submerge(pipette, well, submerge_mm, channel_offset, submerge_speed)
        _aspirate_on_submerge() if aspirate else _dispense_on_submerge()

        # PHASE 3: RETRACT
        callbacks.on_retracting()
        _retract(ctx, pipette, well, channel_offset, retract_mm, retract_speed, _z_disc)
        _aspirate_on_retract() if aspirate else _dispense_on_retract()

    # EXIT
    callbacks.on_exiting()
    hw_api.retract(hw_mount)


def mix_with_liquid_class(
    ctx: ProtocolContext,
    pipette: InstrumentContext,
    tip_volume: int,
    mix_volume: float,
    well: Well,
    channel_offset: Point,
    channel_count: int,
    liquid_tracker: LiquidTracker,
    callbacks: PipettingCallbacks,
    blank: bool = False,
    touch_tip: bool = False,
) -> None:
    """Mix with liquid class."""
    liquid_class = get_liquid_class(
        int(pipette.max_volume), pipette.channels, tip_volume, int(mix_volume)
    )
    _pipette_with_liquid_settings(
        ctx,
        pipette,
        liquid_class,
        well,
        channel_offset,
        channel_count,
        liquid_tracker,
        callbacks,
        mix=mix_volume,
        blank=blank,
        touch_tip=touch_tip,
    )


def aspirate_with_liquid_class(
    ctx: ProtocolContext,
    pipette: InstrumentContext,
    tip_volume: int,
    aspirate_volume: float,
    well: Well,
    channel_offset: Point,
    channel_count: int,
    liquid_tracker: LiquidTracker,
    callbacks: PipettingCallbacks,
    blank: bool = False,
    touch_tip: bool = False,
) -> None:
    """Aspirate with liquid class."""
    liquid_class = get_liquid_class(
        int(pipette.max_volume), pipette.channels, tip_volume, int(aspirate_volume)
    )
    _pipette_with_liquid_settings(
        ctx,
        pipette,
        liquid_class,
        well,
        channel_offset,
        channel_count,
        liquid_tracker,
        callbacks,
        aspirate=aspirate_volume,
        blank=blank,
        touch_tip=touch_tip,
    )


def dispense_with_liquid_class(
    ctx: ProtocolContext,
    pipette: InstrumentContext,
    tip_volume: int,
    dispense_volume: float,
    well: Well,
    channel_offset: Point,
    channel_count: int,
    liquid_tracker: LiquidTracker,
    callbacks: PipettingCallbacks,
    blank: bool = False,
    added_blow_out: bool = True,
    touch_tip: bool = False,
) -> None:
    """Dispense with liquid class."""
    liquid_class = get_liquid_class(
        int(pipette.max_volume), pipette.channels, tip_volume, int(dispense_volume)
    )
    _pipette_with_liquid_settings(
        ctx,
        pipette,
        liquid_class,
        well,
        channel_offset,
        channel_count,
        liquid_tracker,
        callbacks,
        dispense=dispense_volume,
        blank=blank,
        added_blow_out=added_blow_out,
        touch_tip=touch_tip,
    )
