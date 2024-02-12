"""Format the csv report for a liquid-sense run."""

import statistics
from hardware_testing.data.csv_report import (
    CSVReport,
    CSVSection,
    CSVLine,
    CSVLineRepeating,
)
from typing import List, Union

"""
CSV Test Report:
 - Serial numbers:
   - Robot
   - Pipette
   - Scale
   - Environment sensor
 - Config:
   - protocol name
   - pipette_volume
   - pipette_mount
   - tip_volume
   - trials
   - plunger direction
   - liquid
   - labware type
   - speed
   - start height offset
 - Trials
    trial-x-{tipsize}ul
 - Results
    {tipsize}ul-average
    {tipsize}ul-cv
    {tipsize}ul-d
"""


def build_serial_number_section() -> CSVSection:
    """Build section."""
    return CSVSection(
        title="SERIAL-NUMBERS",
        lines=[
            CSVLine("robot", [str]),
            CSVLine("git_description", [str]),
            CSVLine("pipette", [str]),
            CSVLine("scale", [str]),
            CSVLine("environment", [str]),
        ],
    )


def build_config_section() -> CSVSection:
    """Build section."""
    return CSVSection(
        title="CONFIG",
        lines=[
            CSVLine("protocol_name", [str]),
            CSVLine("pipette_volume", [str]),
            CSVLine("tip_volume", [bool, bool, bool]),
            CSVLine("trials", [str]),
            CSVLine("plunger_direction", [str]),
            CSVLine("liquid", [str]),
            CSVLine("labware_type", [str]),
            CSVLine("speed", [str]),
            CSVLine("start_height_offset", [str]),
        ],
    )


def build_trials_section(trials: int, tips: List[int]) -> CSVSection:
    """Build section."""
    lines: List[Union[CSVLine, CSVLineRepeating]] = [
        CSVLine("trial_number", [str, str, str, str, str, str, str, str])
    ]
    lines.extend(
        [
            CSVLine(
                f"trial-baseline-{tip}ul",
                [float, float, float, float, float, float, float, float],
            )
            for tip in tips
        ]
    )
    lines.extend(
        [
            CSVLine(
                f"trial-{t + 1}-{tip}ul",
                [float, float, float, float, float, float, float, float],
            )
            for tip in tips
            for t in range(trials)
        ]
    )

    return CSVSection(
        title="TRIALS",
        lines=lines,
    )


def build_results_section(tips: List[int]) -> CSVSection:
    """Build section."""
    lines: List[CSVLine] = []
    for tip in tips:
        lines.append(CSVLine(f"{tip}ul-average", [float]))
        lines.append(CSVLine(f"{tip}ul-minumum", [float]))
        lines.append(CSVLine(f"{tip}ul-maximum", [float]))
        lines.append(CSVLine(f"{tip}ul-stdev", [float]))
        lines.append(CSVLine(f"{tip}ul-adjusted-average", [float]))
        lines.append(CSVLine(f"{tip}ul-adjusted-minumum", [float]))
        lines.append(CSVLine(f"{tip}ul-adjusted-maximum", [float]))
        lines.append(CSVLine(f"{tip}ul-adjusted-stdev", [float]))
    return CSVSection(title="RESULTS", lines=lines)  # type: ignore[arg-type]


def store_serial_numbers(
    report: CSVReport,
    robot: str,
    pipette: str,
    scale: str,
    environment: str,
    git_description: str,
) -> None:
    """Report serial numbers."""
    report("SERIAL-NUMBERS", "robot", [robot])
    report("SERIAL-NUMBERS", "git_description", [git_description])
    report("SERIAL-NUMBERS", "pipette", [pipette])
    report("SERIAL-NUMBERS", "scale", [scale])
    report("SERIAL-NUMBERS", "environment", [environment])


def store_config(
    report: CSVReport,
    protocol_name: str,
    pipette_volume: str,
    tip_volumes: List[int],
    trials: int,
    plunger_direction: str,
    liquid: str,
    labware_type: str,
    speed: str,
    start_height_offset: str,
) -> None:
    """Report config."""
    report("CONFIG", "protocol_name", [protocol_name])
    report("CONFIG", "pipette_volume", [pipette_volume])
    report(
        "CONFIG",
        "tip_volume",
        [50 in tip_volumes, 200 in tip_volumes, 1000 in tip_volumes],
    )
    report("CONFIG", "trials", [trials])
    report("CONFIG", "plunger_direction", [plunger_direction])
    report("CONFIG", "liquid", [liquid])
    report("CONFIG", "labware_type", [labware_type])
    report("CONFIG", "speed", [speed])
    report("CONFIG", "start_height_offset", [start_height_offset])


def store_baseline_trial(
    report: CSVReport,
    tip: float,
    height: float,
    humidity: float,
    temp: float,
    z_travel: float,
    tip_length_error: float,
) -> None:
    """Report Trial."""
    report(
        "TRIALS",
        f"trial-baseline-{tip}ul",
        [
            height,
            0,
            humidity,
            temp,
            z_travel,
            0,
            0,
            height,
        ],
    )


def store_trial(
    report: CSVReport,
    trial: int,
    tip: float,
    height: float,
    plunger_pos: float,
    humidity: float,
    temp: float,
    z_travel: float,
    plunger_travel: float,
    tip_length_offset: float,
) -> None:
    """Report Trial."""
    report(
        "TRIALS",
        f"trial-{trial + 1}-{tip}ul",
        [
            height,
            plunger_pos,
            humidity,
            temp,
            z_travel,
            plunger_travel,
            tip_length_offset,
            height + tip_length_offset,
        ],
    )


def store_tip_results(
    report: CSVReport, tip: float, results: List[float], adjusted_results: List[float]
) -> None:
    """Store final results."""
    report("RESULTS", f"{tip}ul-average", [sum(results) / len(results)])
    report("RESULTS", f"{tip}ul-minumum", [min(results)])
    report("RESULTS", f"{tip}ul-maximum", [max(results)])
    report("RESULTS", f"{tip}ul-stdev", [statistics.stdev(results)])
    report(
        "RESULTS",
        f"{tip}ul-adjusted-average",
        [sum(adjusted_results) / len(adjusted_results)],
    )
    report("RESULTS", f"{tip}ul-adjusted-minumum", [min(adjusted_results)])
    report("RESULTS", f"{tip}ul-adjusted-maximum", [max(adjusted_results)])
    report("RESULTS", f"{tip}ul-adjusted-stdev", [statistics.stdev(adjusted_results)])


def build_ls_report(
    test_name: str, run_id: str, trials: int, tips: List[int]
) -> CSVReport:
    """Generate a CSV Report."""
    report = CSVReport(
        test_name=test_name,
        sections=[
            build_serial_number_section(),
            build_config_section(),
            build_trials_section(trials, tips),
            build_results_section(tips),
        ],
        run_id=run_id,
        start_time=0.0,
    )
    report(
        "TRIALS",
        "trial_number",
        [
            "height",
            "plunger_pos",
            "humidity",
            "temp",
            "z_travel",
            "plunger_travel",
            "tip_length_offset",
            "adjusted_height",
        ],
    )
    return report
