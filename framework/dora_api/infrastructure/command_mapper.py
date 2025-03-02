from typing import get_type_hints

from domain.exceptions.mapping_error import MappingError


def get_input_port_from_command(command, input_port_type):
    """
    Maps attributes from a command object to an input port object.

    Args:
        command (object): The command object containing attributes to be mapped.
        input_port_type (type): The type of the input port object to be created.

    Returns:
        object: An instance of input_port_type with attributes copied from the command object.

    Exceptions:
        Raises a `MappingError` when a command attribute is not found on the input port type.
    """
    _InputPort = input_port_type()

    for _AttributeName, _AttributeValue in command.__dict__.items():
        if _AttributeName not in get_type_hints(input_port_type).keys():
            raise MappingError(f"Command attribute '{_AttributeName}' not found in input port type '{input_port_type}'.")
        setattr(_InputPort, _AttributeName, _AttributeValue)

    return _InputPort
