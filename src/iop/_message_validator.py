import dataclasses
from typing import Any, Type


def is_message_instance(obj: Any) -> bool:
    """Check if object is a valid Message instance."""
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
    name = f"{klass.__module__}.{klass.__qualname__}"
    if name in ("iop.Message", "grongier.pex.Message"): 
        return True
    return any(is_message_class(c) for c in klass.__bases__)


def is_pickle_message_class(klass: Type) -> bool:
    """Check if class is a PickleMessage type."""
    name = f"{klass.__module__}.{klass.__qualname__}"
    if name in ("iop.PickleMessage", "grongier.pex.PickleMessage"):
        return True
    return any(is_pickle_message_class(c) for c in klass.__bases__)
