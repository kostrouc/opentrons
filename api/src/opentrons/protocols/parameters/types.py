import csv
from typing import TypeVar, Union, TypedDict, TextIO, Optional, List, Any

from .exceptions import RuntimeParameterRequired, ParameterValueError


# TODO(jbl 2024-08-02) This is a public facing class and as such should be moved to the protocol_api folder
class CSVParameter:
    """
    An object representing a CSV file to be used as a runtime parameter.

    .. versionadded:: 2.20
    """

    def __init__(self, csv_file: Optional[TextIO]) -> None:
        self._file = csv_file
        self._contents: Optional[str] = None

    @property
    def file(self) -> TextIO:
        """Returns the file handler for the CSV file.

        The file is treated as read-only, UTF-8-encoded text.
        """
        if self._file is None:
            raise RuntimeParameterRequired(
                "CSV parameter needs to be set to a file for full analysis or protocol run."
            )
        return self._file

    @property
    def contents(self) -> str:
        """Returns the full contents of the CSV file as a single string."""
        if self._contents is None:
            self.file.seek(0)
            self._contents = self.file.read()
        return self._contents

    def parse_as_csv(
        self, detect_dialect: bool = True, **kwargs: Any
    ) -> List[List[str]]:
        """Parses the CSV data and returns a list of lists.

        Each item in the parent list corresponds to a row in the CSV file.
        If the CSV has a header, that will be the first row in the list: ``.parse_as_csv()[0]``.

        Each item in the child lists corresponds to a single cell within its row.
        The data for each cell is represented as a string, even if it is numeric in nature.
        Cast these strings to integers or floating point numbers, as appropriate, to use
        them as inputs to other API methods.

        :param detect_dialect: If ``True``, examine the file and try to assign it a
            :py:class:`csv.Dialect` to improve parsing behavior.
        :param kwargs: For advanced CSV handling, you can pass any of the
            `formatting parameters <https://docs.python.org/3/library/csv.html#csv-fmt-params>`_
            accepted by :py:func:`csv.reader` from the Python standard library.
        """
        rows: List[List[str]] = []
        if detect_dialect:
            try:
                self.file.seek(0)
                dialect = csv.Sniffer().sniff(self.file.read(1024))
                self.file.seek(0)
                reader = csv.reader(self.file, dialect, **kwargs)
            except (UnicodeDecodeError, csv.Error):
                raise ParameterValueError(
                    "Cannot parse dialect or contents from provided CSV file."
                )
        else:
            try:
                reader = csv.reader(self.file, **kwargs)
            except (UnicodeDecodeError, csv.Error):
                raise ParameterValueError("Cannot parse provided CSV file.")
        try:
            for row in reader:
                rows.append(row)
        except (UnicodeDecodeError, csv.Error):
            raise ParameterValueError("Cannot parse provided CSV file.")
        self.file.seek(0)
        return rows


PrimitiveAllowedTypes = Union[str, int, float, bool]
AllAllowedTypes = Union[str, int, float, bool, TextIO, None]
UserFacingTypes = Union[str, int, float, bool, CSVParameter]

ParamType = TypeVar("ParamType", bound=AllAllowedTypes)


class ParameterChoice(TypedDict):
    """A parameter choice containing the display name and value."""

    display_name: str
    value: PrimitiveAllowedTypes
