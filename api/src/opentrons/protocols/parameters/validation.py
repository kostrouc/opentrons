import keyword
from typing import List, Optional, Union, Literal

from .types import (
    AllowedTypes,
    ParamType,
    ParameterChoice,
    ParameterNameError,
    ParameterValueError,
    ParameterDefinitionError,
)


UNIT_MAX_LEN = 10
DISPLAY_NAME_MAX_LEN = 30
DESCRIPTION_MAX_LEN = 100


def ensure_display_name(display_name: str) -> str:
    """Validate display name is within the character limit."""
    if len(display_name) > DISPLAY_NAME_MAX_LEN:
        raise ParameterNameError(
            f"Display name {display_name} greater than {DISPLAY_NAME_MAX_LEN} characters."
        )
    return display_name


def ensure_variable_name(variable_name: str) -> str:
    """Validate variable name is a valid python variable name."""
    if not variable_name.isidentifier():
        raise ParameterNameError(
            "Variable name must only contain alphanumeric characters, underscores, and cannot start with a digit."
        )
    if keyword.iskeyword(variable_name):
        raise ParameterNameError("Variable name cannot be a reserved Python keyword.")
    return variable_name


def ensure_description(description: Optional[str]) -> Optional[str]:
    """Validate description is within the character limit."""
    if description is not None and len(description) > DESCRIPTION_MAX_LEN:
        raise ParameterNameError(
            f"Description {description} greater than {DESCRIPTION_MAX_LEN} characters."
        )
    return description


def ensure_unit_string_length(unit: Optional[str]) -> Optional[str]:
    """Validate unit is within the character limit."""
    if unit is not None and len(unit) > UNIT_MAX_LEN:
        raise ParameterNameError(
            f"Description {unit} greater than {UNIT_MAX_LEN} characters."
        )
    return unit


def ensure_value_type(
    value: Union[float, bool, str], parameter_type: type
) -> AllowedTypes:
    """Ensures that the value type coming in from the client matches the given type.

    This does not guarantee that the value will be the correct type for the given parameter, only that any data coming
    in is in the format that we expect. For now, the only transformation it is doing is converting integers represented
    as floating points to integers. If something is labelled as an int but is not actually an integer, that will be
    caught when it is attempted to be set as the parameter value and will raise the appropriate error there.
    """
    validated_value: AllowedTypes
    if isinstance(value, float) and parameter_type is int and value.is_integer():
        validated_value = int(value)
    else:
        validated_value = value
    return validated_value


def convert_type_string_for_enum(
    parameter_type: type,
) -> Literal["int", "float", "str"]:
    """Converts a type object into a string for an enumerated parameter."""
    if parameter_type is int:
        return "int"
    elif parameter_type is float:
        return "float"
    elif parameter_type is str:
        return "str"
    else:
        raise ParameterValueError(
            f"Cannot resolve parameter type {parameter_type} for an enumerated parameter."
        )


def convert_type_string_for_num_param(parameter_type: type) -> Literal["int", "float"]:
    """Converts a type object into a string for a number parameter."""
    if parameter_type is int:
        return "int"
    elif parameter_type is float:
        return "float"
    else:
        raise ParameterValueError(
            f"Cannot resolve parameter type {parameter_type} for a number parameter."
        )


def _validate_choices(
    minimum: Optional[ParamType],
    maximum: Optional[ParamType],
    choices: List[ParameterChoice],
    parameter_type: type,
) -> None:
    """Validate that min and max is not defined and all choices are properly formatted."""
    if minimum is not None or maximum is not None:
        raise ParameterDefinitionError(
            "If choices are provided minimum and maximum values cannot be provided."
        )
    for choice in choices:
        try:
            display_name = choice["display_name"]
            value = choice["value"]
        except KeyError:
            raise ParameterDefinitionError(
                "All choices must be a dictionary with keys 'display_name' and 'value'."
            )
        ensure_display_name(display_name)
        if not isinstance(value, parameter_type):
            raise ParameterDefinitionError(
                f"All choices provided must match type {type(parameter_type)}"
            )


def _validate_min_and_max(
    minimum: Optional[ParamType],
    maximum: Optional[ParamType],
    parameter_type: type,
) -> None:
    """Validate the minium and maximum are both defined, the same type, and a valid range."""
    if minimum is not None and maximum is None:
        raise ParameterDefinitionError(
            "If a minimum value is provided a maximum must also be provided."
        )
    elif maximum is not None and minimum is None:
        raise ParameterDefinitionError(
            "If a maximum value is provided a minimum must also be provided."
        )
    elif maximum is not None and minimum is not None:
        if isinstance(maximum, (int, float)) and isinstance(minimum, (int, float)):
            if maximum <= minimum:
                raise ParameterDefinitionError(
                    "Maximum must be greater than the minimum"
                )

            if not isinstance(minimum, parameter_type) or not isinstance(
                maximum, parameter_type
            ):
                raise ParameterDefinitionError(
                    f"Minimum and maximum must match type {parameter_type}"
                )
        else:
            raise ParameterDefinitionError(
                "Only parameters of type float or int can have a minimum and maximum"
            )


def validate_type(value: ParamType, parameter_type: type) -> None:
    """Validate parameter value is the correct type."""
    if not isinstance(value, parameter_type):
        raise ParameterValueError(
            f"Parameter value has type {type(value)} must match type {parameter_type}."
        )


def validate_options(
    default: ParamType,
    minimum: Optional[ParamType],
    maximum: Optional[ParamType],
    choices: Optional[List[ParameterChoice]],
    parameter_type: type,
) -> None:
    """Validate default values and all possible constraints for a valid parameter definition."""
    validate_type(default, parameter_type)

    if choices is None and minimum is None and maximum is None:
        raise ParameterDefinitionError(
            "Must provide either choices or a minimum and maximum value"
        )

    if choices is not None:
        _validate_choices(minimum, maximum, choices, parameter_type)
    else:
        _validate_min_and_max(minimum, maximum, parameter_type)