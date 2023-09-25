"""Liquid Probe OT3."""
import argparse
import asyncio

from opentrons_shared_data.labware import load_definition

from hardware_testing.opentrons_api.types import Point, OT3Mount, InstrumentProbeType
from hardware_testing.opentrons_api import helpers_ot3

from hardware_testing.gravimetric.config import _get_liquid_probe_settings

TIP_RACK_SLOT = 3
LABWARE_SLOT = 2

PROBE_OFFSET = {
    1: {
        InstrumentProbeType.PRIMARY: Point(x=0, y=0, z=0),
    },
    8: {
        InstrumentProbeType.PRIMARY: Point(x=0, y=0, z=0),
        InstrumentProbeType.SECONDARY: Point(x=0, y=9 * 7, z=0),
    },
    96: {
        InstrumentProbeType.PRIMARY: Point(x=0, y=0, z=0),
        InstrumentProbeType.SECONDARY: Point(x=9 * -11, y=9 * 7, z=0),
    },
}


async def _main(
    is_simulating: bool,
    mount: OT3Mount,
    tip: int,
    probe: InstrumentProbeType,
    labware: str,
) -> None:

    # CREATE API
    api = await helpers_ot3.build_async_ot3_hardware_api(
        is_simulating=is_simulating, pipette_left="p1000_single_v3.5"
    )
    await api.retract(mount)

    # GATHER VARIABLES
    pip = api.hardware_pipettes[mount.to_mount()]
    tip_pos = helpers_ot3.get_theoretical_a1_position(
        TIP_RACK_SLOT, f"opentrons_flex_96_tiprack_{tip}ul"
    )
    tip_length = helpers_ot3.get_default_tip_length(tip)
    labware_def = load_definition(loadname=labware, version=1)
    labware_well_depth = labware_def["wells"]["A1"]["depth"]
    labware_well_top = helpers_ot3.get_theoretical_a1_position(LABWARE_SLOT, labware)
    labware_well_top += PROBE_OFFSET[int(pip.channels)][probe]
    probe_settings = _get_liquid_probe_settings(
        pip.channels,
        int(pip.working_volume),
        tip,
        labware_well_top.z,
        labware_well_depth,
    )

    # PICK-UP-TIP
    await helpers_ot3.move_to_arched_ot3(api, mount, tip_pos)
    await api.pick_up_tip(mount, tip_length=tip_length)
    await api.retract(mount)

    # LIQUID-PROBE
    print(f"about to probe liquid in well A1 of labware {labware}")
    if not api.is_simulator:
        input("press ENTER to continue: ")
    await helpers_ot3.move_to_arched_ot3(api, mount, labware_well_top)
    found_z = await api.liquid_probe(mount, probe_settings, probe)
    liquid_height = found_z - (labware_well_top.z - labware_well_depth)
    print(f"found height in well: {round(liquid_height, 1)} mm")
    await api.retract()

    # RETURN-TIP
    await helpers_ot3.move_to_arched_ot3(api, mount, tip_pos - Point(z=-10))
    await api.drop_tip(mount)
    await api.retract(mount)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--tip", type=int, choices=[50, 200, 1000], required=True)
    parser.add_argument(
        "--probe", type=str, choices=["primary", "secondary"], default="primary"
    )
    parser.add_argument("--mount", type=str, choices=["left", "right"], default="left")
    args = parser.parse_args()
    asyncio.run(
        _main(
            args.simulate,
            mount={"left": OT3Mount.LEFT, "right": OT3Mount.RIGHT}[args.mount],
            tip=args.tip,
            probe={
                "primary": InstrumentProbeType.PRIMARY,
                "secondary": InstrumentProbeType.SECONDARY,
            }[args.probe],
            labware="nest_12_reservoir_15ml",
        )
    )
