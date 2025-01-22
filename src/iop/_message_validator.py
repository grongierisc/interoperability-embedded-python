import dataclasses
from typing import Any, Type
from pydantic import BaseModel
from iop._message import _Message


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
    if is_pickle_message_class(type(obj)):
        return True
    return False


def is_iris_object_instance(obj: Any) -> bool:
    """Check if object is an IRIS persistent object."""
    return (obj is not None and 
            type(obj).__module__.startswith('iris') and 
            obj._IsA("%Persistent"))


def is_message_class(klass: Type) -> bool:
    """Check if class is a Message type."""
    if issubclass(klass, BaseModel):
        return True
    if issubclass(klass, _Message):
        return True
    return False



def is_pickle_message_class(klass: Type) -> bool:
    """Check if class is a PickleMessage type."""
    name = f"{klass.__module__}.{klass.__qualname__}"
    if name in ("iop.PickleMessage", "grongier.pex.PickleMessage"):
        return True
    return any(is_pickle_message_class(c) for c in klass.__bases__)
