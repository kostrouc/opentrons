"""Deck configuration resource provider."""
from typing import List, Set, Tuple, Optional

from opentrons_shared_data.deck.dev_types import DeckDefinitionV4, CutoutFixture

from ..types import (
    AddressableArea,
    PotentialCutoutFixture,
    DeckPoint,
    Dimensions,
    AddressableOffsetVector,
    LabwareOffsetVector,
)
from ..errors import (
    CutoutDoesNotExistError,
    FixtureDoesNotExistError,
    AddressableAreaDoesNotExistError,
    FixtureDoesNotProvideAreasError,
)


def get_cutout_fixture_by_id(
    cutout_fixture_id: str, deck_definition: DeckDefinitionV4
) -> CutoutFixture:
    """Gets cutout fixture from deck that matches the cutout fixture ID provided."""
    for cutout_fixture in deck_definition["cutoutFixtures"]:
        if cutout_fixture["id"] == cutout_fixture_id:
            return cutout_fixture
    raise FixtureDoesNotExistError(
        f"Could not find cutout fixture with name {cutout_fixture_id}"
    )


def get_potential_cutout_fixtures(
    addressable_area_name: str, deck_definition: DeckDefinitionV4
) -> Tuple[str, Set[PotentialCutoutFixture]]:
    """Given an addressable area name, gets the cutout ID associated with it and a set of potential fixtures."""
    potential_fixtures = []
    for cutout_fixture in deck_definition["cutoutFixtures"]:
        for cutout_id, provided_areas in cutout_fixture[
            "providesAddressableAreas"
        ].items():
            if addressable_area_name in provided_areas:
                potential_fixtures.append(
                    PotentialCutoutFixture(
                        cutout_id=cutout_id,
                        cutout_fixture_id=cutout_fixture["id"],
                    )
                )
    # This following logic is making the assumption that every addressable area can only go on one cutout, though
    # it may have multiple cutout fixtures that supply it on that cutout. If this assumption changes, some of the
    # following logic will have to be readjusted
    assert (
        potential_fixtures
    ), f"No potential fixtures for addressable area {addressable_area_name}"
    cutout_id = potential_fixtures[0].cutout_id
    assert all(cutout_id == fixture.cutout_id for fixture in potential_fixtures)
    return cutout_id, set(potential_fixtures)


def get_cutout_position(cutout_id: str, deck_definition: DeckDefinitionV4) -> DeckPoint:
    """Get the base position of a cutout on the deck."""
    for cutout in deck_definition["locations"]["cutouts"]:
        if cutout_id == cutout["id"]:
            position = cutout["position"]
            return DeckPoint(x=position[0], y=position[1], z=position[2])
    else:
        raise CutoutDoesNotExistError(f"Could not find cutout with name {cutout_id}")


def get_addressable_area_from_name(
    addressable_area_name: str,
    cutout_position: DeckPoint,
    deck_definition: DeckDefinitionV4,
) -> AddressableArea:
    """Given a name and a cutout position, get an addressable area on the deck."""
    for addressable_area in deck_definition["locations"]["addressableAreas"]:
        if addressable_area["id"] == addressable_area_name:
            area_offset = addressable_area["offsetFromCutoutFixture"]
            position = AddressableOffsetVector(
                x=cutout_position.x + area_offset[0],
                y=cutout_position.y + area_offset[1],
                z=cutout_position.z + area_offset[2],
            )
            bounding_box = Dimensions(
                x=addressable_area["boundingBox"]["xDimension"],
                y=addressable_area["boundingBox"]["yDimension"],
                z=addressable_area["boundingBox"]["zDimension"],
            )
            drop_tips_deck_offset = addressable_area.get("dropTipsOffset")
            drop_tips_offset: Optional[LabwareOffsetVector]
            if drop_tips_deck_offset:
                drop_tips_offset = LabwareOffsetVector(
                    x=drop_tips_deck_offset[0],
                    y=drop_tips_deck_offset[1],
                    z=drop_tips_deck_offset[2],
                )
            else:
                drop_tips_offset = None

            drop_labware_deck_offset = addressable_area.get("dropLabwareOffset")
            drop_labware_offset: Optional[LabwareOffsetVector]
            if drop_labware_deck_offset:
                drop_labware_offset = LabwareOffsetVector(
                    x=drop_labware_deck_offset[0],
                    y=drop_labware_deck_offset[1],
                    z=drop_labware_deck_offset[2],
                )
            else:
                drop_labware_offset = None

            return AddressableArea(
                area_name=addressable_area["id"],
                display_name=addressable_area["displayName"],
                bounding_box=bounding_box,
                position=position,
                compatible_module_types=[],  # TODO figure out getting this correct later
                drop_tip_offset=drop_tips_offset,
                drop_labware_offset=drop_labware_offset,
            )
    raise AddressableAreaDoesNotExistError(
        f"Could not find addressable area with name {addressable_area_name}"
    )


def get_addressable_areas_from_cutout_and_cutout_fixture(
    cutout_id: str, cutout_fixture: CutoutFixture, deck_definition: DeckDefinitionV4
) -> List[AddressableArea]:
    """Get all provided addressable areas for a given cutout fixture and associated cutout."""
    base_position = get_cutout_position(cutout_id, deck_definition)

    try:
        provided_areas = cutout_fixture["providesAddressableAreas"][cutout_id]
    except KeyError:
        raise FixtureDoesNotProvideAreasError(
            f"Cutout fixture {cutout_fixture['id']} does not provide addressable areas for {cutout_id}"
        )

    return [
        get_addressable_area_from_name(
            addressable_area_name, base_position, deck_definition
        )
        for addressable_area_name in provided_areas
    ]
