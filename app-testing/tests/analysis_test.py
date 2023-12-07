import json
from pathlib import Path
from typing import List

import pytest
from syrupy.extensions.json import JSONSnapshotExtension
from syrupy.filters import props
from syrupy.types import SerializableData

exclude = props(
    "id",
    "createdAt",
    "startedAt",
    "completedAt",
    "lastModified",
    "created",
    "key",
    "pipetteId",
    "labwareId",
    "serialNumber",
    "moduleId",
    "liquidId",
)

ignore_test = ["OT2_P300M_P20S_MM_TM_TC1_5_2_6_PD40Erroranalysis","OT3_P1000MLeft_P50MRight_HS_MM_TC_TM_2_15_ABR3_Illumina_DNA_Enrichment_v4analysis","OT3_P1000MLeft_P50MRight_HS_TM_MM_TC_2_15_ABR4_Illumina_DNA_Prep_24xanalysis"]

@pytest.fixture
def snapshot_exclude(snapshot: SerializableData) -> SerializableData:
    return snapshot.with_defaults(exclude=exclude)


@pytest.fixture
def snapshot_json(snapshot_exclude: SerializableData) -> SerializableData:
    return snapshot_exclude.with_defaults(extension_class=JSONSnapshotExtension)


def get_analyses(stem_keyword: str) -> List[Path]:
    path = Path(
        Path(__file__).parent.parent,
        "analysis_results",
    )
    return [file for file in path.glob("*.json") if stem_keyword in file.stem]


def test_analysis_json(snapshot_json: SerializableData) -> None:
    base_stem_keyword = "_v7.0.2_"
    alpha_stem_keyword = "_v7.1.0-alpha.2_"
    base = get_analyses(base_stem_keyword)
    new = get_analyses(alpha_stem_keyword)
    print("\n")
    print(f"Base files: {len(base)}")
    print(f"New files: {len(new)}")
    to_use = new  # change me for snapshot
    files_no_exist = []
    for file in to_use:
        if file.exists():
            with open(file, "r") as f:
                data = json.load(f)
                test_name = file.stem.replace(base_stem_keyword, "")
                test_name = test_name.replace(alpha_stem_keyword, "")
                print(f"Test name: {test_name}")
            if test_name not in ignore_test:
                assert snapshot_json(name=test_name) == data
        else:
            files_no_exist.append(file)
    print(f"Files that do not exist: {files_no_exist}")
