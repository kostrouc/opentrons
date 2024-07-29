"""Measure Tip Overlap."""
from typing import List, Tuple, Optional, Any
from abr_testing.automation import google_sheets_tool
from opentrons.protocol_api import (
    ProtocolContext,
    Labware,
    Well,
    InstrumentContext,
)

from opentrons_shared_data.pipette.load_data import load_definition
from opentrons_shared_data.pipette.types import (
    PipetteChannelType,
    PipetteModelType,
    PipetteVersionType,
)

###########################################
#  VARIABLES - START
###########################################
# TODO: use runtime-variables instead of constants
NUM_TRIALS = 10

TIP_SIZE = 50
PIPETTE_SIZE = 50
PIPETTE_CHANNELS = 1

LABWARE = "corning_96_wellplate_360ul_flat"

SLOT_TIPRACK = "D3"
SLOT_LABWARE = "D1"
SLOT_DIAL = "B3"

###########################################
#  VARIABLES - END
###########################################

metadata = {"protocolName": "lld-test-empty-wells"}
requirements = {"robotType": "Flex", "apiLevel": "2.20"}

TEST_WELLS = {
    1: {
        "corning_96_wellplate_360ul_flat": ["A1", "A12", "H1", "H12"],
    },
    8: {
        "corning_96_wellplate_360ul_flat": ["A1", "A12"],
    },
    96: {
        "corning_96_wellplate_360ul_flat": ["A1"],
    },
}

DIAL_POS_WITHOUT_TIP: Optional[float] = None
DIAL_PORT_NAME = "/dev/ttyUSB0"
DIAL_PORT = None
RUN_ID = ""
FILE_NAME = ""
CSV_HEADER = "some,dumb,header"


def _setup(ctx: ProtocolContext) -> Tuple[InstrumentContext, Labware, Labware, Labware, Optional[Any]]:
    global DIAL_PORT, RUN_ID, FILE_NAME
    # TODO: use runtime-variables instead of constants
    ctx.load_trash_bin("A3")
    pip_name = f"flex_{PIPETTE_CHANNELS}channel_{PIPETTE_SIZE}"
    rack_name = f"opentrons_flex_96_tiprack_{TIP_SIZE}uL"

    rack = ctx.load_labware(rack_name, SLOT_TIPRACK)
    pipette = ctx.load_instrument(pip_name, "left")
    labware = ctx.load_labware(LABWARE, SLOT_LABWARE)
    dial = ctx.load_labware("dial_indicator", SLOT_DIAL)
    
    google_sheet = None

    if not ctx.is_simulating() and DIAL_PORT is None:
        from hardware_testing.data import create_file_name, create_run_id
        from hardware_testing.drivers.mitutoyo_digimatic_indicator import (
            Mitutoyo_Digimatic_Indicator,
        )

        DIAL_PORT = Mitutoyo_Digimatic_Indicator(port=DIAL_PORT_NAME)
        DIAL_PORT.connect()
        RUN_ID = create_run_id()
        FILE_NAME = create_file_name(
            metadata["protocolName"], RUN_ID, f"{pip_name}-{rack_name}"
        )
        _write_line_to_csv(ctx, RUN_ID)
        _write_line_to_csv(ctx, pip_name)
        _write_line_to_csv(ctx, rack_name)
        _write_line_to_csv(ctx, LABWARE)
        # get the minimum LLD height configured for this pipette
        pip_model_list = pipette.model.split("_")
        pip_def = load_definition(
            model=PipetteModelType(pip_model_list[0]),
            channels=PipetteChannelType(pipette.channels),
            version=PipetteVersionType(
                major=int(pip_model_list[-1][-3]),
                minor=int(pip_model_list[-1][-1])
            ),
        )
        # Writes details about test run to google sheet.
        header = [["Run ID", "Pipette Name", "Tip Type", "Labware"], [RUN_ID, pip_name, rack_name, LABWARE]]
        try:
            google_sheet = _set_up_google_sheet(ctx, header)
        except google_sheets_tool.google_interaction_error:
            ctx.comment("Did not connect to google sheet.")
            google_sheet = None
        tipVolume = "t" + str(TIP_SIZE)
        lld_min_height = pip_def.lld_settings[tipVolume]["minHeight"]
        _write_line_to_csv(ctx, f"lld-min-height,{lld_min_height}")
        if google_sheet is not None: 
            _write_line_to_google_sheet(ctx, google_sheet, ["lld-min-height", lld_min_height])

    return pipette, rack, labware, dial, google_sheet

def _set_up_google_sheet(ctx:ProtocolContext, header:List[List[str]]) -> Optional[Any]:
    """Connect to google sheet using credentials file in jupyter notebook."""
    if ctx.is_simulating():
        return
    credentials_path = "/var/lib/jupyter/notebooks/abr.json"
    try:
        google_sheet = google_sheets_tool.google_sheet(
            credentials_path, "Empty Well Testing", tab_number=0
        )
        sheet_id = google_sheet.create_worksheet(RUN_ID)  # type: ignore[union-attr]
        google_sheet.batch_update_cells(header, "A", 1, sheet_id)
        ctx.comment("Connected to the google sheet.")
        return google_sheet
    except:
        ctx.comment(
            "There are no google sheets credentials. Make sure credentials in jupyter notebook."
        )
        
def _write_line_to_google_sheet(ctx: ProtocolContext,google_sheet:Any, line: str)-> None:
    if ctx.is_simulating():
        return
    try:
        google_sheet.update_row(line)
    except:
        ctx.comment("Google sheet not updated.")

def _write_line_to_csv(ctx: ProtocolContext, line: str) -> None:
    if ctx.is_simulating():
        return
    from hardware_testing.data import append_data_to_file

    append_data_to_file(metadata["protocolName"], RUN_ID, FILE_NAME, f"{line}\n")


def _get_test_wells(labware: Labware, pipette: InstrumentContext) -> List[Well]:
    return [labware[w] for w in TEST_WELLS[pipette.channels][labware.load_name]]


def _get_test_tips(rack: Labware, pipette: InstrumentContext) -> List[Well]:
    if pipette.channels == 96:
        test_tips = [rack["A1"]]
    elif pipette.channels == 8:
        test_tips = rack.rows()[0][:NUM_TRIALS]
    else:
        test_tips = rack.wells()[:NUM_TRIALS]
    return test_tips


def _read_dial_indicator(
    ctx: ProtocolContext, pipette: InstrumentContext, dial: Labware
) -> float:
    pipette.move_to(dial["A1"].top())
    ctx.delay(seconds=2)
    if ctx.is_simulating():
        return 0.0
    return DIAL_PORT.read()


def _store_dial_baseline(
    ctx: ProtocolContext, pipette: InstrumentContext, dial: Labware, google_sheet: Any
) -> None:
    global DIAL_POS_WITHOUT_TIP
    if DIAL_POS_WITHOUT_TIP is not None:
        return
    DIAL_POS_WITHOUT_TIP = _read_dial_indicator(ctx, pipette, dial)
    _write_line_to_csv(ctx, f"DIAL-BASELINE,{DIAL_POS_WITHOUT_TIP}")
    _write_line_to_google_sheet(google_sheet, ["DIAL-BASELINE", DIAL_POS_WITHOUT_TIP])

def _get_tip_z_error(
    ctx: ProtocolContext, pipette: InstrumentContext, dial: Labware
) -> float:
    assert DIAL_POS_WITHOUT_TIP is not None
    new_val = _read_dial_indicator(ctx, pipette, dial)
    z_error = new_val - DIAL_POS_WITHOUT_TIP
    # NOTE: dial-indicators are upside-down, so we need to flip the values
    return z_error * -1.0


def _get_wells_with_expected_liquid_state(
    ctx: ProtocolContext, pipette: InstrumentContext, test_wells: List[Well], expected_state: bool
) -> List[Well]:
    successful_wells = []
    for well in test_wells:
        pipette.move_to(well.top())
        ctx.pause()
        found_liquid = pipette.detect_liquid_presence(well)
        ctx.pause()
        if found_liquid == expected_state:
            successful_wells.append(well)
    return successful_wells


def _test_for_expected_liquid_state(
    ctx: ProtocolContext,
    pipette: InstrumentContext,
    dial: Labware,
    tips: List[Well],
    wells: List[Well],
    trials: int,
    liquid_state: bool,
    google_sheet: Any
) -> None:
    fail_counter = 0
    trial_counter = 0
    _store_dial_baseline(ctx, pipette, dial, google_sheet)
    csv_header = f'trial,result,tip-z-error,{",".join([w.well_name for w in wells])}'
    _write_line_to_csv(ctx, f"{csv_header}")
    _write_line_to_google_sheet(ctx, google_sheet, )
    while trial_counter < trials:
        for tip in tips:
            trial_counter += 1
            # NOTE: (sigler) prioritize testing all-tip pickups over partial-tip pickups
            pipette.pick_up_tip(tip)
            tip_z_error = _get_tip_z_error(ctx, pipette, dial)
            successful_wells = _get_wells_with_expected_liquid_state(ctx,
                pipette, wells, liquid_state
            )
            all_trials_passed = "PASS" if len(successful_wells) == len(wells) else "FAIL"
            trial_data = [trial_counter, all_trials_passed, tip_z_error]
            each_well_result_bool = [bool(w in successful_wells) for w in wells]
            trial_data += ["PASS" if w else "FAIL" for w in each_well_result_bool]
            _write_line_to_csv(ctx, ",".join([str(d) for d in trial_data]))
            pipette.drop_tip()
            fail_counter += 0 if all_trials_passed else 1
        if trial_counter < trials:
            ctx.pause("replace with NEW tips")
            pipette.reset_tipracks()
    ctx.pause(f"NOTE: total failed wells = {fail_counter}/{trial_counter}")


def run(ctx: ProtocolContext) -> None:
    """Run."""
    pipette, rack, labware, dial, google_sheet = _setup(ctx)
    test_wells = _get_test_wells(labware, pipette)
    test_tips = _get_test_tips(rack, pipette)
    _test_for_expected_liquid_state(
        ctx,
        pipette,
        dial,
        tips=test_tips,
        wells=test_wells,
        trials=NUM_TRIALS,
        liquid_state=False,
        google_sheet
    )
