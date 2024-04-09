"""Calculate plunger max flow-rates."""
import argparse
import asyncio
from typing import Optional, List, cast
from pathlib import Path

from opentrons.calibration_storage.types import (
    SourceType,
    CalibrationStatus,
)
from opentrons.config.robot_configs import default_pipette_offset
from opentrons.config.defaults_ot3 import DEFAULT_MAX_SPEEDS
from opentrons.config.defaults_ot2 import B_MAX_SPEED, C_MAX_SPEED
from opentrons.hardware_control.instruments.ot2.pipette import Pipette
from opentrons.hardware_control.instruments.ot2.instrument_calibration import (
    PipetteOffsetByPipetteMount,
)
from opentrons.hardware_control.types import OT3AxisKind
from opentrons.types import Point

from opentrons_shared_data.pipette import (
    pipette_load_name_conversions as pipette_load_name,
    mutable_configurations,
)
from opentrons_shared_data.pipette import model_config
from opentrons_shared_data.pipette.dev_types import PipetteModel


VOLUMES = {
    20: [1, 10, 20],
    50: [1, 10, 50],
    300: [20, 150, 300],
    1000: [10, 100, 500, 1000]
}


def _get_spec_volumes(pipette: Pipette) -> List[float]:
    for s in VOLUMES.keys():
        if f"p{s}" in pipette.model:
            return VOLUMES[s]
    raise ValueError()


def _gather_models() -> List[str]:
    cfg = model_config()["config"]
    found_pips = list(cfg.keys())
    found_pips.sort()
    return found_pips


def _is_it_a_real_pipette(model: str) -> bool:
    accepted_sizes = [f"p{s}" for s in VOLUMES.keys()]
    if not sum([1 for m in accepted_sizes if m in model]):
        return False
    if not sum([1 for m in ["v2", "v3"] if m in model]):
        return False
    if ".0" in model:
        return False
    return True


def _load_pipette(model: str) -> Optional[Pipette]:
    pipette_model = pipette_load_name.convert_pipette_model(
        cast(PipetteModel, model)
    )
    try:
        configurations = mutable_configurations.load_with_mutable_configurations(
            pipette_model, Path("fake/path"), "testiId"
        )
        pip_cal_obj = PipetteOffsetByPipetteMount(
            offset=Point(*default_pipette_offset()),
            source=SourceType.default,
            status=CalibrationStatus(),
        )
        pip = Pipette(config=configurations, pipette_offset_cal=pip_cal_obj)
        return pip
    except (FileNotFoundError, KeyError) as e:
        # print(f"ERROR: [{model}] {e}")
        return None


def _load_all_pipettes() -> List[Pipette]:
    pips: List[Pipette] = []
    for model in _gather_models():
        if not _is_it_a_real_pipette(model):
            continue
        pipette = _load_pipette(model)
        if pipette:
            pips.append(pipette)
    return pips


def _get_plunger_max_speed(pipette: Pipette) -> float:
    assert B_MAX_SPEED == C_MAX_SPEED
    if "v2" in pipette.model:
        return B_MAX_SPEED
    elif "v3" in pipette.model:
        if "96" in pipette.model:
            return DEFAULT_MAX_SPEEDS.high_throughput[OT3AxisKind.P]
        else:
            return DEFAULT_MAX_SPEEDS.low_throughput[OT3AxisKind.P]


def _get_max_flow_rate_at_volume(pipette: Pipette, volume: float) -> float:
    max_speed = _get_plunger_max_speed(pipette)
    ul_per_mm = pipette.ul_per_mm(volume, "dispense")
    return round(ul_per_mm * max_speed, 1)


async def _main() -> None:
    print("--------------COPY PASTE BELOW INTO GOOGLE SHEET---------------")
    print("model\tvolume\tmax-flow-rate")
    for pipette in _load_all_pipettes():
        for volume in _get_spec_volumes(pipette):
            flow_rate = _get_max_flow_rate_at_volume(pipette, volume)
            print(f"{pipette.model}\t{volume}\t{flow_rate}")
    print("--------------          DONE                   ---------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    asyncio.run(_main())
