from opentrons_shared_data.robot.dev_types import RobotType

from opentrons.config import feature_flags

from opentrons.protocol_reader.protocol_source import (
    ProtocolConfig,
    PythonProtocolConfig,
    JsonProtocolConfig,
)
from opentrons.protocols.api_support.types import APIVersion


# TODO(mm, 2023-05-10): Deduplicate these constants with
# opentrons.protocol_engine.types.DeckType and consider moving to shared-data.
SHORT_TRASH_DECK = "ot2_short_trash"
STANDARD_OT2_DECK = "ot2_standard"
STANDARD_OT3_DECK = "ot3_standard"


LOAD_FIXED_TRASH_GATE_VERSION_PYTHON = APIVersion(2, 15)
# TODO(jbl 2023-10-26) potentially replace using schema version in JSON protocols with another/new field
LOAD_FIXED_TRASH_GATE_VERSION_JSON = 7


def should_load_fixed_trash(protocol_config: ProtocolConfig) -> bool:
    """Decide whether to automatically load fixed trash on the deck based on version."""
    load_fixed_trash = False
    if isinstance(protocol_config, PythonProtocolConfig):
        load_fixed_trash = (
            protocol_config.api_version <= LOAD_FIXED_TRASH_GATE_VERSION_PYTHON
        )
    elif isinstance(protocol_config, JsonProtocolConfig):
        load_fixed_trash = (
            protocol_config.schema_version <= LOAD_FIXED_TRASH_GATE_VERSION_JSON
        )

    return load_fixed_trash


def guess_from_global_config() -> str:
    """Return the deck type that the host device physically has.

    This only makes sense when the software is running on a real robot.

    When simulating or analyzing a protocol, especially off-robot, don't use this, because it may
    not match the protocol's declared robot type. Use `for_analysis` instead.
    """
    if feature_flags.enable_ot3_hardware_controller():
        return STANDARD_OT3_DECK
    elif feature_flags.short_fixed_trash():
        return SHORT_TRASH_DECK
    else:
        return STANDARD_OT2_DECK


def for_simulation(robot_type: RobotType) -> str:
    """Return the deck type that should be used for simulating and analyzing a protocol.

    Params:
        robot_type: The robot type that the protocol is meant to run on.
    """
    if robot_type == "OT-2 Standard":
        # OT-2 protocols don't have a way of defining whether they're meant to run on a short-trash
        # or standard deck. So when we're simulating an OT-2 protocol, we need to make an
        # arbitrary choice for which deck type to use.
        return STANDARD_OT2_DECK
    elif robot_type == "OT-3 Standard":
        # OT-3s currently only have a single deck type.
        return STANDARD_OT3_DECK
