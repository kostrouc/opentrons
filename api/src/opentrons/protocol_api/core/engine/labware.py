"""ProtocolEngine-based Labware core implementations."""
from typing import List, Optional, cast

from opentrons_shared_data.labware.dev_types import (
    LabwareParameters as LabwareParametersDict,
    LabwareDefinition as LabwareDefinitionDict,
)

from opentrons.protocol_engine.clients import SyncClient as ProtocolEngineClient
from opentrons.protocols.geometry.labware_geometry import LabwareGeometry
from opentrons.protocols.api_support.tip_tracker import TipTracker
from opentrons.types import Point

from ..labware import AbstractLabware, LabwareLoadParams
from .well import WellCore


class LabwareCore(AbstractLabware[WellCore]):
    """Labware API core using a ProtocolEngine.

    Args:
        labware_id: ProtocolEngine ID of the loaded labware.
        engine_client: ProtocolEngine synchronous client.
    """

    def __init__(self, labware_id: str, engine_client: ProtocolEngineClient) -> None:
        self._labware_id = labware_id
        self._engine_client = engine_client

        labware_state = engine_client.state.labware
        self._definition = labware_state.get_definition(labware_id)
        self._user_display_name = labware_state.get_display_name(labware_id)

    @property
    def labware_id(self) -> str:
        """The labware's unique ProtocolEngine ID."""
        return self._labware_id

    @property
    def highest_z(self) -> float:
        raise NotImplementedError("LabwareCore.highest_z not implemented")

    @property
    def separate_calibration(self) -> bool:
        raise NotImplementedError("LabwareCore.separate_calibration not implemented")

    @property
    def load_name(self) -> str:
        return self._definition.parameters.loadName

    def get_uri(self) -> str:
        """Get the URI string string of the labware's definition.

        The URI is unique for a given namespace, load name, and definition version.
        """
        return self._engine_client.state.labware.get_definition_uri(self._labware_id)

    def get_load_params(self) -> LabwareLoadParams:
        return LabwareLoadParams(
            namespace=self._definition.namespace,
            load_name=self._definition.parameters.loadName,
            version=self._definition.version,
        )

    def get_display_name(self) -> str:
        """Get a display name for the labware, falling back to the definition."""
        return self._user_display_name or self._definition.metadata.displayName

    def get_user_display_name(self) -> Optional[str]:
        """Get the user-specified display name of the labware, if set."""
        return self._user_display_name

    def get_name(self) -> str:
        raise NotImplementedError("LabwareCore.get_name not implemented")

    def set_name(self, new_name: str) -> None:
        raise NotImplementedError("LabwareCore.set_name not implemented")

    def get_definition(self) -> LabwareDefinitionDict:
        """Get the labware's definition as a plain dictionary."""
        return cast(LabwareDefinitionDict, self._definition.dict(exclude_none=True))

    def get_parameters(self) -> LabwareParametersDict:
        return cast(
            LabwareParametersDict,
            self._definition.parameters.dict(exclude_none=True),
        )

    def get_quirks(self) -> List[str]:
        raise NotImplementedError("LabwareCore.get_quirks not implemented")

    def set_calibration(self, delta: Point) -> None:
        # TODO(jbl 2022-09-01): implement set calibration through the engine
        pass

    def get_calibrated_offset(self) -> Point:
        raise NotImplementedError("LabwareCore.get_calibrated_offset not implemented")

    def is_tip_rack(self) -> bool:
        "Whether the labware is a tip rack."
        return self._definition.parameters.isTiprack

    def is_fixed_trash(self) -> bool:
        """Whether the labware is a fixed trash."""
        return self._engine_client.state.labware.is_fixed_trash(
            labware_id=self.labware_id
        )

    def get_tip_length(self) -> float:
        raise NotImplementedError("LabwareCore.get_tip_length not implemented")

    def set_tip_length(self, length: float) -> None:
        raise NotImplementedError("LabwareCore.set_tip_length not implemented")

    def reset_tips(self) -> None:
        self._engine_client.reset_tips(labware_id=self.labware_id)

    def get_next_tip(
        self, num_tips: int, starting_tip: Optional[WellCore]
    ) -> Optional[str]:
        return self._engine_client.state.tips.get_next_tip(
            labware_id=self._labware_id,
            use_column=num_tips != 1,
            starting_tip_name=(
                starting_tip.get_name()
                if starting_tip and starting_tip.labware_id == self._labware_id
                else None
            ),
        )

    # TODO(mc, 2022-11-09): remove from engine core
    def get_tip_tracker(self) -> TipTracker:
        raise NotImplementedError("LabwareCore.get_tip_tracker not implemented")

    def get_well_columns(self) -> List[List[str]]:
        """Get the all well names, organized by column, from the labware's definition."""
        return self._definition.ordering

    def get_geometry(self) -> LabwareGeometry:
        raise NotImplementedError("LabwareCore.get_geometry not implemented")

    def get_default_magnet_engage_height(
        self, preserve_half_mm: bool = False
    ) -> Optional[float]:
        raise NotImplementedError(
            "LabwareCore.get_default_magnet_engage_height not implemented"
        )

    def get_well_core(self, well_name: str) -> WellCore:
        """Create a well core interface to a well in this labware."""
        return WellCore(
            name=well_name,
            labware_id=self._labware_id,
            engine_client=self._engine_client,
        )
