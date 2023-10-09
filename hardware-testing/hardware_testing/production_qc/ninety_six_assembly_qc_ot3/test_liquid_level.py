"""Test Liquid Level Detection."""
from typing import List, Union, Tuple, Optional, Dict

from opentrons.config.types import LiquidProbeSettings
from opentrons.hardware_control.ot3api import OT3API
from opentrons.hardware_control.types import InstrumentProbeType
from opentrons_shared_data.labware import load_definition

from hardware_testing.data import ui
from hardware_testing.data.csv_report import (
    CSVReport,
    CSVResult,
    CSVLine,
    CSVLineRepeating,
)
from hardware_testing.gravimetric.config import _get_liquid_probe_settings
from hardware_testing.opentrons_api import helpers_ot3
from hardware_testing.opentrons_api.types import OT3Mount, Point, Axis

LABWARE = "corning_96_wellplate_360ul_flat"
PRIMARY_LABWARE_SLOT = 3
SECONDARY_LABWARE_SLOT = 6
TIP_RACK_LIST = [
    {"tip": 1000, "slot": 9, 'slot_name': 'B3'},
    {"tip": 200, "slot": 8, 'slot_name': 'B2'},
    {"tip": 50, "slot": 7, 'slot_name': 'B1'},
]
SENSORS_LIST = [
    {"labware": PRIMARY_LABWARE_SLOT, "probe": InstrumentProbeType.PRIMARY},
    {"labware": SECONDARY_LABWARE_SLOT, "probe": InstrumentProbeType.SECONDARY},
]
LABWARE_SENSOR_WELLS = {"PRIMARY": "A1", "SECONDARY": "H12"}
SLOTS = {3: "D3", 6: "C3"}
TRIALS = 3


def _get_test_tag(probe: object, tip: int, trial: int) -> str:
    return f"{probe.name.lower()}-{tip}-{trial}"


def build_csv_lines() -> List[Union[CSVLine, CSVLineRepeating]]:
    """Build CSV Lines."""
    lines: List[Union[CSVLine, CSVLineRepeating]] = list()
    for probe in SENSORS_LIST:
        for tip in TIP_RACK_LIST:
            for trial in range(TRIALS):
                tag = _get_test_tag(probe["probe"], tip["tip"], trial + 1)
                # Data: Jogged Z, Sensed Z, Error, Pass/Fail
                lines.append(CSVLine(tag, [float, float, float, CSVResult]))

    return lines  # type: ignore[return-value]

tip_rack_pos = Point()
async def run(api: OT3API, report: CSVReport, section: str) -> None:
    """Run."""

    pip = api.hardware_pipettes[OT3Mount.LEFT.to_mount()]

    async def sense_labware(
        labware_slot: int, probe: InstrumentProbeType, tip: int, trial: int
    ) -> None:
        ui.print_header(f"TESTING {probe.name} SENSOR - TIP:{tip}uL - TRIAL:{trial}")

        # Jog to Labware
        labware_def = load_definition(loadname=LABWARE, version=1)
        labware_well_depth = labware_def["wells"]["A1"]["depth"]
        labware_well_top = helpers_ot3.get_theoretical_a1_position(
            labware_slot, LABWARE
        )
        print("Homing plunger...")
        await api.home([Axis.P_L])
        if not api.is_simulator:
            ui.get_user_ready(f"about to move to labware {SLOTS[labware_slot]}")
        await helpers_ot3.move_to_arched_ot3(
            api, OT3Mount.LEFT, labware_well_top + Point(z=3.5)
        )
        print(f"Jog to liquid in well {LABWARE_SENSOR_WELLS[probe.name]}")
        await helpers_ot3.jog_mount_ot3(api, OT3Mount.LEFT)
        jogged_labware = await api.gantry_position(OT3Mount.LEFT)
        jogged_z = round(jogged_labware.z, 3)
        print(f"JOGGED LIQUID Z: {jogged_z}")

        # Prepare to liquid probe
        await helpers_ot3.move_to_arched_ot3(
            api, OT3Mount.LEFT, jogged_labware + Point(z=8)
        )
        print("Blowing out pipette...")
        pip.blow_out_flow_rate = 2000
        await api.blow_out(OT3Mount.LEFT)

        # Liquid Level Probe
        probe_settings = _get_liquid_probe_settings(
            pip.channels,
            int(pip.working_volume),
            tip,
            labware_well_top.z + 8,
            labware_well_depth + 5,
        )
        if not api.is_simulator:
            ui.get_user_ready(
                f"about to liquid probe {probe_settings.max_z_distance}mm down"
            )
        sensed_z = round(
            await api.liquid_probe(OT3Mount.LEFT, probe_settings, probe), 3
        )
        print(f"SENSED LIQUID Z: {sensed_z}")
        error_z = round(sensed_z - jogged_z, 3)
        print(f"ERROR Z: {error_z}")

        # Record Data
        report(
            section,
            _get_test_tag(probe, tip, trial),
            [jogged_z, sensed_z, error_z, CSVResult.PASS],
        )

        await api.retract(OT3Mount.LEFT)

    async def test_tip(tip: int, tip_rack_slot: int, trial: int) -> None:
        ui.print_header(f"TESTING {tip}uL TIPS - TRIAL:{trial}")
        # Pick up tips
        if not api.is_simulator:
            ui.get_user_ready(f"Move to {tip}uL tiprack")

        global tip_rack_pos
        if trial == 1:
            tip_rack_pos = helpers_ot3.get_theoretical_a1_position(tip_rack_slot, f"opentrons_flex_96_tiprack_{tip}ul")
            await helpers_ot3.move_to_arched_ot3(api, OT3Mount.LEFT, tip_rack_pos + Point(z=23))
            print("jog to PICK-UP-TIP location:")
            await helpers_ot3.jog_mount_ot3(api, OT3Mount.LEFT)
            tip_rack_pos = await api.gantry_position(OT3Mount.LEFT)
        else:
            await helpers_ot3.move_to_arched_ot3(api, OT3Mount.LEFT, tip_rack_pos)

        tip_length = helpers_ot3.get_default_tip_length(tip)
        await api.pick_up_tip(OT3Mount.LEFT, tip_length=tip_length)
        await api.retract(OT3Mount.LEFT)

        for s in SENSORS_LIST:
            await sense_labware(s["labware"], s["probe"], tip, trial)

        # Return tips
        await helpers_ot3.move_to_arched_ot3(
            api, OT3Mount.LEFT, tip_rack_pos - Point(z=10)
        )
        await api.drop_tip(OT3Mount.LEFT)
        await api.retract(OT3Mount.LEFT)

        if not api.is_simulator:
            prompt_1 = f"Replace {tip}uL tips in positions {LABWARE_SENSOR_WELLS['PRIMARY']} and {LABWARE_SENSOR_WELLS['SECONDARY']}"
            prompt_2 = f"Replace Labware in slots {SLOTS[PRIMARY_LABWARE_SLOT]} and {SLOTS[SECONDARY_LABWARE_SLOT]}"
            ui.get_user_ready(prompt_1 + '\n' + prompt_2)

    print("Place Labware for Liquid level test:")
    for tip_type in TIP_RACK_LIST:
        print(f"\t{tip_type['tip']}uL tiprack in slot {tip_type['slot_name']}")
    print(f"\t{LABWARE} in slot {SLOTS[PRIMARY_LABWARE_SLOT]} with 400uL in well {LABWARE_SENSOR_WELLS['PRIMARY']}")
    print(f"\t{LABWARE} in slot {SLOTS[SECONDARY_LABWARE_SLOT]} with 400uL in well {LABWARE_SENSOR_WELLS['SECONDARY']}")

    for tip_type in TIP_RACK_LIST:
        for _trial in range(TRIALS):
            trial = _trial + 1  # _trial is 0 indexed
            await test_tip(tip_type["tip"], tip_type["slot"], trial)
        if not api.is_simulator:
            ui.get_user_ready(f"Replace {tip}uL tips in positions {LABWARE_SENSOR_WELLS['PRIMARY']} and {LABWARE_SENSOR_WELLS['SECONDARY']}")