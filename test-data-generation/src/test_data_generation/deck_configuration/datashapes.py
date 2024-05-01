"""Data shapes for the deck configuration of a Flex."""

import enum
import dataclasses
import typing

ColumnName = typing.Literal["1", "2", "3"]
RowName = typing.Literal["a", "b", "c", "d"]
SlotName = typing.Literal[
    "a1", "a2", "a3", "b1", "b2", "b3", "c1", "c2", "c3", "d1", "d2", "d3"
]


class PossibleSlotContents(enum.Enum):
    """Possible contents of a slot on a Flex."""

    # Implicitly defined fixtures
    THERMOCYCLER_MODULE = enum.auto()
    WASTE_CHUTE = enum.auto()
    WASTE_CHUTE_NO_COVER = enum.auto()
    STAGING_AREA = enum.auto()
    STAGING_AREA_WITH_WASTE_CHUTE = enum.auto()
    STAGING_AREA_WITH_WASTE_CHUTE_NO_COVER = enum.auto()
    STAGING_AREA_WITH_MAGNETIC_BLOCK = enum.auto()

    # Explicitly defined fixtures
    MAGNETIC_BLOCK_MODULE = enum.auto()
    TEMPERATURE_MODULE = enum.auto()
    HEATER_SHAKER_MODULE = enum.auto()
    TRASH_BIN = enum.auto()

    # Other
    LABWARE_SLOT = enum.auto()

    @classmethod
    def longest_string(cls) -> int:
        """Return the longest string representation of the slot content."""
        length = max([len(e.name) for e in PossibleSlotContents])
        return length if length % 2 == 0 else length + 1

    def __str__(self) -> str:
        """Return a string representation of the slot content."""
        return f"{self.name.replace('_', ' ')}"
    
    @classmethod
    def all(cls) -> typing.List["PossibleSlotContents"]:
        """Return all possible slot contents."""
        return list(cls)
    
    @property
    def modules(self) -> typing.List["PossibleSlotContents"]:
        """Return the modules."""
        return [
            PossibleSlotContents.THERMOCYCLER_MODULE,
            PossibleSlotContents.MAGNETIC_BLOCK_MODULE,
            PossibleSlotContents.TEMPERATURE_MODULE,
            PossibleSlotContents.HEATER_SHAKER_MODULE,
        ]
    
    @property
    def staging_areas (self) -> typing.List["PossibleSlotContents"]:
        """Return the staging areas."""
        return [
            PossibleSlotContents.STAGING_AREA,
            PossibleSlotContents.STAGING_AREA_WITH_WASTE_CHUTE,
            PossibleSlotContents.STAGING_AREA_WITH_WASTE_CHUTE_NO_COVER,
            PossibleSlotContents.STAGING_AREA_WITH_MAGNETIC_BLOCK,
        ]
    
    @property
    def waste_chutes(self) -> typing.List["PossibleSlotContents"]:
        """Return the waste chutes."""
        return [
            PossibleSlotContents.WASTE_CHUTE,
            PossibleSlotContents.WASTE_CHUTE_NO_COVER,
            PossibleSlotContents.STAGING_AREA_WITH_WASTE_CHUTE,
            PossibleSlotContents.STAGING_AREA_WITH_WASTE_CHUTE_NO_COVER,
        ]

    def is_a_module(self) -> bool:
        """Return True if the slot contains a module."""
        return any([self is module for module in self.modules])
    
    def is_module_or_trash_bin(self) -> bool:
        """Return True if the slot contains a module or trash bin."""
        return self.is_a_module() or self is PossibleSlotContents.TRASH_BIN

    def is_a_staging_area(self) -> bool:
        """Return True if the slot contains a staging area."""
        return any([self is staging_area for staging_area in self.staging_areas])

    def is_a_waste_chute(self) -> bool:
        """Return True if the slot contains a waste chute."""
        return any([self is waste_chute for waste_chute in self.waste_chutes])


@dataclasses.dataclass
class Slot:
    """A slot on a Flex."""

    row: RowName
    col: ColumnName
    contents: PossibleSlotContents

    def __str__(self) -> str:
        """Return a string representation of the slot."""
        return f"{(self.row + self.col).center(self.contents.longest_string())}{self.contents}"

    @property
    def __label(self) -> SlotName:
        """Return the slot label."""
        return typing.cast(SlotName, f"{self.row}{self.col}")

    @property
    def slot_label_string(self) -> str:
        """Return the slot label."""
        return f"{self.__label.center(self.contents.longest_string())}"

    @property
    def contents_string(self) -> str:
        """Return the slot contents."""
        return f"{str(self.contents).center(self.contents.longest_string())}"


@dataclasses.dataclass
class Row:
    """A row of slots on a Flex."""

    row: RowName

    col1: Slot
    col2: Slot
    col3: Slot

    def __str__(self) -> str:
        """Return a string representation of the row."""
        return f"{self.col1}{self.col2}{self.col3}"

    def slot_by_col_number(self, name: ColumnName) -> Slot:
        """Return the slot by name."""
        return getattr(self, f"col{name}")  # type: ignore

    @property
    def slots(self) -> typing.List[Slot]:
        """Iterate over the slots in the row."""
        return [self.col1, self.col2, self.col3]

    def __len__(self) -> int:
        """Return the number of slots in the row."""
        return len(self.slots)
    
    def update_slot(self, slot: Slot) -> None:
        """Update the slot in the row."""
        setattr(self, f"col{slot.col}", slot)


@dataclasses.dataclass
class Column:
    """A column of slots on a Flex."""

    col: ColumnName

    a: Slot
    b: Slot
    c: Slot
    d: Slot

    def __str__(self) -> str:
        """Return a string representation of the column."""
        return f"{self.a}{self.b}{self.c}{self.d}"

    @property
    def slots(self) -> typing.List[Slot]:
        """Return the slots in the column."""
        return [self.a, self.b, self.c, self.d]

    def slot_by_row(self, name: RowName) -> Slot:
        """Return the slot by name."""
        return getattr(self, f"{name}")

    def number_of(self, contents: PossibleSlotContents) -> int:
        """Return the number of slots with the contents."""
        return len([True for slot in self.slots if slot.contents is contents])

    def slot_above(self, slot: Slot) -> typing.Optional[Slot]:
        """Return the slot above the passed slot."""
        index = self.slots.index(slot)
        if index == 0:
            return None
        return self.slots[index - 1]

    def slot_below(self, slot: Slot) -> typing.Optional[Slot]:
        """Return the slot below the passed slot."""
        index = self.slots.index(slot)
        if index == 3:
            return None
        return self.slots[index + 1]


@dataclasses.dataclass
class DeckConfiguration:
    """The deck on a Flex."""

    a: Row
    b: Row
    c: Row
    d: Row

    def __str__(self) -> str:
        """Return a string representation of the deck."""
        string_list = []
        dashed_line = "-" * (PossibleSlotContents.longest_string() * 3)
        equal_line = "=" * (PossibleSlotContents.longest_string() * 3)
        for row in self.rows:
            string_list.append(
                " | ".join([slot.slot_label_string for slot in row.slots])
            )
            string_list.append(" | ".join([slot.contents_string for slot in row.slots]))
            if row != self.d:
                string_list.append(dashed_line)
        joined_string = "\n".join(string_list)

        return f"\n{joined_string}\n\n{equal_line}"

    def __hash__(self) -> int:
        """Return the hash of the deck."""
        return hash(tuple(slot.contents.value for slot in self.slots))

    def __eq__(self, other: typing.Any) -> bool:
        """Return True if the deck is equal to the other deck."""
        if not isinstance(other, DeckConfiguration):
            return False
        return all(
            slot.contents == other_slot.contents
            for slot in self.slots
            for other_slot in other.slots
        )
    
    @classmethod
    def from_cols(cls, col1: Column, col2: Column, col3: Column) -> "DeckConfiguration":
        """Create a deck configuration from columns."""
        return cls(
            a=Row("a", col1.a, col2.a, col3.a),
            b=Row("b", col1.b, col2.b, col3.b),
            c=Row("c", col1.c, col2.c, col3.c),
            d=Row("d", col1.d, col2.d, col3.d),
        )
    
    @property
    def rows(self) -> typing.List[Row]:
        """Return the rows of the deck."""
        return [self.a, self.b, self.c, self.d]

    def row_by_name(self, name: RowName) -> Row:
        """Return the row by name."""
        return getattr(self, name)  # type: ignore

    @property
    def slots(self) -> typing.List[Slot]:
        """Return the slots of the deck."""
        return [slot for row in self.rows for slot in row.slots]

    def slot_above(self, slot: Slot) -> typing.Optional[Slot]:
        """Return the slot above the passed slot."""
        row_index = self.rows.index(self.row_by_name(slot.row))
        if row_index == 0:
            return None
        return self.rows[row_index - 1].slot_by_col_number(slot.col)

    def slot_below(self, slot: Slot) -> typing.Optional[Slot]:
        """Return the slot below the passed slot."""
        row_index = self.rows.index(self.row_by_name(slot.row))
        if row_index == 3:
            return None
        return self.rows[row_index + 1].slot_by_col_number(slot.col)

    def number_of(self, contents: PossibleSlotContents) -> int:
        """Return the number of slots with the contents."""
        return len([True for slot in self.slots if slot.contents is contents])

    def override_with_column(self, column: Column) -> None:
        """Override the deck configuration with the column."""
        for row in self.rows:
            new_value = column.slot_by_row(row.row)
            row.update_slot(new_value)

    def column_by_number(self, number: ColumnName) -> Column:
        """Return the column by number."""
        return Column(
            col=number,
            a=self.a.slot_by_col_number(number),
            b=self.b.slot_by_col_number(number),
            c=self.c.slot_by_col_number(number),
            d=self.d.slot_by_col_number(number),
        )