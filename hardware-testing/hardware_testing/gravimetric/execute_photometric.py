"""Gravimetric."""
from typing import Tuple, List, Dict
from math import ceil

from opentrons.protocol_api import ProtocolContext, Well, Labware

from hardware_testing.data import ui
from hardware_testing.opentrons_api.types import Point
from .measurement import (
    MeasurementType,
    create_measurement_tag,
    EnvironmentData,
)
from .measurement.environment import read_environment_data
from . import report
from . import config
from .helpers import (
    _jog_to_find_liquid_height,
    _apply_labware_offsets,
    _pick_up_tip,
    _drop_tip,
)
from .trial import (
    PhotometricTrial,
    build_photometric_trials,
    TestResources,
)
from .liquid_class.pipetting import (
    aspirate_with_liquid_class,
    dispense_with_liquid_class,
    PipettingCallbacks,
)
from .liquid_height.height import LiquidTracker

from .tips import get_tips


_MEASUREMENTS: List[Tuple[str, EnvironmentData]] = list()

_DYE_MAP: Dict[str, Dict[str, float]] = {
    "HV": {"min": 200.1, "max": 350},
    "A": {"min": 50, "max": 200},
    "B": {"min": 10, "max": 49.99},
    "C": {"min": 2, "max": 9.999},
    "D": {"min": 1, "max": 1.999},
}
_MIN_START_VOLUME_UL = 30000
_MIN_END_VOLUME_UL = 10000
_MAX_VOLUME_UL = 165000


def _get_dye_type(volume: float) -> str:
    dye_type = None
    for dye in _DYE_MAP.keys():
        if volume >= _DYE_MAP[dye]["min"] and volume <= _DYE_MAP[dye]["max"]:
            dye_type = dye
            break
    assert (
        dye_type is not None
    ), f"volume {volume} is outside of the available dye range"
    return dye_type


def _load_labware(
    ctx: ProtocolContext, cfg: config.PhotometricConfig
) -> Tuple[Labware, Labware]:
    print(f'Loading photoplate labware: "{cfg.photoplate}"')
    photoplate = ctx.load_labware(cfg.photoplate, location=cfg.photoplate_slot)
    reservoir = ctx.load_labware(cfg.reservoir, location=cfg.reservoir_slot)
    _apply_labware_offsets(cfg, [photoplate, reservoir])
    return photoplate, reservoir


def _dispense_volumes(volume: float) -> Tuple[float, float, int]:
    num_dispenses = ceil(volume / 250)
    volume_to_dispense = volume / num_dispenses
    target_volume = min(max(volume_to_dispense, 200), 250)
    return target_volume, volume_to_dispense, num_dispenses


def _run_trial(trial: PhotometricTrial) -> None:
    """Aspirate dye and dispense into a photometric plate."""

    def _no_op() -> None:
        """Do Nothing."""
        return

    def _tag(m_type: MeasurementType) -> str:
        return create_measurement_tag(m_type, trial.volume, 0, trial.trial)

    def _record_measurement_and_store(m_type: MeasurementType) -> EnvironmentData:
        m_tag = _tag(m_type)
        m_data = read_environment_data(
            trial.cfg.pipette_mount, trial.ctx.is_simulating()
        )
        report.store_measurements_pm(trial.test_report, m_tag, m_data)
        _MEASUREMENTS.append(
            (
                m_tag,
                m_data,
            )
        )
        return m_data

    pipetting_callbacks = PipettingCallbacks(
        on_submerging=_no_op,
        on_mixing=_no_op,
        on_aspirating=_no_op,
        on_dispensing=_no_op,
        on_retracting=_no_op,
        on_blowing_out=_no_op,
        on_exiting=_no_op,
    )

    channel_count = 96
    # RUN INIT
    target_volume, volume_to_dispense, num_dispenses = _dispense_volumes(trial.volume)
    photoplate_preped_vol = max(target_volume - volume_to_dispense, 0)

    if num_dispenses > 1 and not trial.ctx.is_simulating():
        # TODO: Likely will not test 1000 uL in the near-term,
        #       but eventually we'll want to be more helpful here in prompting
        #       what volumes need to be added between trials.
        ui.get_user_ready("check DYE is enough")

    _record_measurement_and_store(MeasurementType.INIT)
    trial.pipette.move_to(location=trial.source.top(), minimum_z_height=133)
    while trial.do_jog:
        required_ul = max(
            (trial.volume * channel_count * trial.cfg.trials) + _MIN_END_VOLUME_UL,
            _MIN_START_VOLUME_UL,
        )
        if not trial.ctx.is_simulating():
            _liquid_height = _jog_to_find_liquid_height(
                trial.ctx, trial.pipette, trial.source
            )
            height_below_top = trial.source.depth - _liquid_height
            print(f"liquid is {height_below_top} mm below top of reservoir")
            trial.liquid_tracker.set_start_volume_from_liquid_height(
                trial.source, _liquid_height, name="Dye"
            )
        else:
            trial.liquid_tracker.set_start_volume(trial.source, required_ul)
        reservoir_ul = trial.liquid_tracker.get_volume(trial.source)
        print(
            f"software thinks there is {round(reservoir_ul / 1000, 1)} mL "
            f"of liquid in the reservoir (required = {round(required_ul / 1000, 1)} ml)"
        )
        if required_ul <= reservoir_ul < _MAX_VOLUME_UL:
            break
        elif required_ul > _MAX_VOLUME_UL:
            raise NotImplementedError(
                f"too many trials ({trial.cfg.trials}) at {trial.volume} uL, "
                f"refilling reservoir is currently not supported"
            )
        elif reservoir_ul < required_ul:
            error_msg = (
                f"not enough volume in reservoir to aspirate {trial.volume} uL "
                f"across {channel_count}x channels for {trial.cfg.trials}x trials"
            )
            if trial.ctx.is_simulating():
                raise ValueError(error_msg)
            ui.print_error(error_msg)
            trial.pipette.move_to(location=trial.source.top(100))
            difference_ul = required_ul - reservoir_ul
            ui.get_user_ready(
                f"ADD {round(difference_ul / 1000.0, 1)} mL more liquid to RESERVOIR"
            )
            trial.pipette.move_to(location=trial.source.top())
        else:
            raise RuntimeError(
                f"bad volume in reservoir: {round(reservoir_ul / 1000, 1)} ml"
            )
    # RUN ASPIRATE
    aspirate_with_liquid_class(
        trial.ctx,
        trial.pipette,
        trial.tip_volume,
        trial.volume,
        trial.source,
        Point(),
        channel_count,
        trial.liquid_tracker,
        callbacks=pipetting_callbacks,
        blank=False,
        inspect=trial.inspect,
        mix=trial.mix,
        touch_tip=False,
    )

    _record_measurement_and_store(MeasurementType.ASPIRATE)
    for i in range(num_dispenses):

        for w in trial.dest.wells():
            trial.liquid_tracker.set_start_volume(w, photoplate_preped_vol)
        trial.pipette.move_to(trial.dest["A1"].top())

        # RUN DISPENSE
        dispense_with_liquid_class(
            trial.ctx,
            trial.pipette,
            trial.tip_volume,
            volume_to_dispense,
            trial.dest["A1"],
            Point(),
            channel_count,
            trial.liquid_tracker,
            callbacks=pipetting_callbacks,
            blank=False,
            inspect=trial.inspect,
            mix=trial.mix,
            added_blow_out=(i + 1) == num_dispenses,
            touch_tip=trial.cfg.touch_tip,
        )
        _record_measurement_and_store(MeasurementType.DISPENSE)
        trial.pipette.move_to(location=trial.dest["A1"].top().move(Point(0, 0, 133)))
        if (i + 1) == num_dispenses:
            _drop_tip(trial.pipette, trial.cfg.return_tip)
        else:
            trial.pipette.move_to(
                location=trial.dest["A1"].top().move(Point(0, 107, 133))
            )
        if not trial.ctx.is_simulating():
            ui.get_user_ready("add SEAL to plate and remove from DECK")
    return


def _display_dye_information(
    cfg: config.PhotometricConfig, resources: TestResources
) -> None:
    ui.print_header("PREPARE")
    dye_types_req: Dict[str, float] = {dye: 0 for dye in _DYE_MAP.keys()}
    for vol in resources.test_volumes:
        _, volume_to_dispense, num_dispenses = _dispense_volumes(vol)
        dye_per_vol = vol * 96 * cfg.trials
        dye_types_req[_get_dye_type(volume_to_dispense)] += dye_per_vol

    include_hv = not [
        v
        for v in resources.test_volumes
        if _DYE_MAP["A"]["min"] <= v < _DYE_MAP["A"]["max"]
    ]

    for dye in dye_types_req.keys():
        transfered_ul = dye_types_req[dye]
        reservoir_ul = max(_MIN_START_VOLUME_UL, transfered_ul + _MIN_END_VOLUME_UL)
        leftover_ul = reservoir_ul - transfered_ul

        def _ul_to_ml(x: float) -> float:
            return round(x / 1000.0, 1)

        if dye_types_req[dye] > 0:
            if cfg.refill:
                # only add the minimum required volume
                print(f' * {_ul_to_ml(leftover_ul)} mL "{dye}" LEFTOVER in reservoir')
                if not resources.ctx.is_simulating():
                    ui.get_user_ready(
                        f'[refill] ADD {_ul_to_ml(transfered_ul)} mL more DYE type "{dye}"'
                    )
            else:
                # add minimum required volume PLUS labware's dead-volume
                if not resources.ctx.is_simulating():
                    dye_msg = 'A" or "HV' if include_hv and dye == "A" else dye
                    ui.get_user_ready(
                        f'add {_ul_to_ml(reservoir_ul)} mL of DYE type "{dye_msg}"'
                    )


def build_pm_report(
    cfg: config.PhotometricConfig, resources: TestResources
) -> report.CSVReport:
    """Build a CSVReport formated for photometric tests."""
    ui.print_header("CREATE TEST-REPORT")
    test_report = report.create_csv_test_report_photometric(
        resources.test_volumes, cfg, run_id=resources.run_id
    )
    test_report.set_tag(resources.pipette_tag)
    test_report.set_operator(resources.operator_name)
    test_report.set_version(resources.git_description)
    report.store_serial_numbers_pm(
        test_report,
        robot=resources.robot_serial,
        pipette=resources.pipette_tag,
        tips=resources.tip_batch,
        environment="None",
        liquid="None",
    )
    return test_report


def execute_trials(
    cfg: config.PhotometricConfig,
    resources: TestResources,
    tips: Dict[int, List[Well]],
    trials: Dict[float, List[PhotometricTrial]],
) -> None:
    """Execute a batch of pre-constructed trials."""

    def _next_tip() -> Well:
        # get the first channel's first-used tip
        # NOTE: note using list.pop(), b/c tip will be re-filled by operator,
        #       and so we can use pick-up-tip from there again
        nonlocal tips
        if not len(tips[0]):
            if not resources.ctx.is_simulating():
                ui.get_user_ready(f"replace TIPRACKS in slots {cfg.slots_tiprack}")
            tips = get_tips(resources.ctx, resources.pipette)
        return tips[0].pop(0)

    trial_total = len(resources.test_volumes) * cfg.trials
    trial_count = 0
    for volume in trials.keys():
        ui.print_title(f"{volume} uL")
        for trial in trials[volume]:
            trial_count += 1
            ui.print_header(f"{volume} uL ({trial.trial + 1}/{cfg.trials})")
            print(f"trial total {trial_count}/{trial_total}")
            if not resources.ctx.is_simulating():
                ui.get_user_ready(f"put PLATE #{trial.trial + 1} and remove SEAL")
            next_tip: Well = _next_tip()
            next_tip_location = next_tip.top()
            _pick_up_tip(
                resources.ctx, resources.pipette, cfg, location=next_tip_location
            )
            _run_trial(trial)


def run(cfg: config.PhotometricConfig, resources: TestResources) -> None:
    """Run."""
    trial_total = len(resources.test_volumes) * cfg.trials

    ui.print_header("LOAD LABWARE")
    photoplate, reservoir = _load_labware(resources.ctx, cfg)
    liquid_tracker = LiquidTracker(resources.ctx)

    tips = get_tips(resources.ctx, resources.pipette)
    total_tips = len([tip for chnl_tips in tips.values() for tip in chnl_tips]) * len(
        resources.test_volumes
    )

    assert (
        trial_total <= total_tips
    ), f"more trials ({trial_total}) than tips ({total_tips})"

    test_report = build_pm_report(cfg, resources)

    _display_dye_information(cfg, resources)

    trials = build_photometric_trials(
        resources.ctx,
        test_report,
        resources.pipette,
        reservoir["A1"],
        photoplate,
        resources.test_volumes,
        liquid_tracker,
        cfg,
    )

    print("homing...")
    resources.ctx.home()
    resources.pipette.home_plunger()

    try:
        execute_trials(cfg, resources, tips, trials)
    finally:
        ui.print_title("CHANGE PIPETTES")
        if resources.pipette.has_tip:
            if resources.pipette.current_volume > 0:
                print("dispensing liquid to trash")
                trash = resources.pipette.trash_container.wells()[0]
                # FIXME: this should be a blow_out() at max volume,
                #        but that is not available through PyAPI yet
                #        so instead just dispensing.
                resources.pipette.dispense(
                    resources.pipette.current_volume, trash.top()
                )
                resources.pipette.aspirate(10)  # to pull any droplets back up
            print("dropping tip")
            _drop_tip(resources.pipette, cfg.return_tip)
        print("moving to attach position")
        resources.pipette.move_to(
            resources.ctx.deck.position_for(5).move(Point(x=0, y=9 * 7, z=150))
        )
