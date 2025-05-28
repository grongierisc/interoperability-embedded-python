import dataclasses
from typing import Any, Type

from ._message import _Message, _PickleMessage, _PydanticPickleMessage, BaseModel


def is_message_instance(obj: Any) -> bool:
    """Check if object is a valid Message instance."""
    if isinstance(obj, BaseModel):
        return True
    if is_message_class(type(obj)):
        if not dataclasses.is_dataclass(obj):
            raise TypeError(f"{type(obj).__module__}.{type(obj).__qualname__} must be a dataclass")
        return True
    return False


def is_pickle_message_instance(obj: Any) -> bool:
    """Check if object is a PickleMessage instance."""
    if isinstance(obj, _PydanticPickleMessage):
        return True
    if is_pickle_message_class(type(obj)):
        return True
    return False


def is_iris_object_instance(obj: Any) -> bool:
    """Check if object is an IRIS persistent object."""
    return (obj is not None and 
            type(obj).__module__.startswith('iris') and 
            (obj._IsA("%Persistent") or obj._IsA("%Stream.Object"))) 
            # Stream.Object are used for HTTP InboundAdapter/OutboundAdapter


def is_message_class(klass: Type) -> bool:
    """Check if class is a Message type."""
    if issubclass(klass, _Message):
        return True
    return False



def is_pickle_message_class(klass: Type) -> bool:
    """Check if class is a PickleMessage type."""
    if issubclass(klass, _PickleMessage):
        return True
    if issubclass(klass, _PydanticPickleMessage):
        return True
    return False
