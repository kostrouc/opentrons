"""Test Liquid Level Detection."""
from asyncio import sleep
from time import time
from typing import List, Union, Tuple, Optional, Dict

from opentrons.hardware_control.ot3api import OT3API
from opentrons.hardware_control.motion_utilities import target_position_from_relative

from hardware_testing.data import ui
from hardware_testing.data.csv_report import (
    CSVReport,
    CSVResult,
    CSVLine,
    CSVLineRepeating,
)
from hardware_testing.opentrons_api import helpers_ot3
from hardware_testing.opentrons_api.types import OT3Mount, Point, Axis



def build_csv_lines() -> List[Union[CSVLine, CSVLineRepeating]]:
    """Build CSV Lines."""
    liquid_level_test = [CSVLine("liquid-level", [float, CSVResult])]

    return liquid_level_test  # type: ignore[return-value]


async def run(api: OT3API, report: CSVReport, section: str) -> None:
    """Run."""

    # Pick up tips

    # Jog to Primary Sensor Labware

    # Liquid Level Probe Primary

    # Jog to secondary Sensor Labware

    # Liquid Level Probe Secondary

    # Return tips