from typing import Any

from pydantic import BaseModel


class _Message:
    """Base class for JSON-serialized messages sent between components.

    This class has no properties or methods. Users subclass Message and add properties.
    """

    _iris_id: str | None = None

    def get_iris_id(self) -> str | None:
        """Get the IRIS ID of the message."""
        return self._iris_id


class _PickleMessage(_Message):
    """Base class for pickle-serialized messages sent between components.

    This class has no properties or methods. Users subclass Message and add properties.
    """

    pass


class _PydanticMessage(BaseModel):
    """Base class for Pydantic-based messages that can be serialized to IRIS."""

    _iris_id: str | None = None

    def __init__(self, **data: Any):
        super().__init__(**data)

    def get_iris_id(self) -> str | None:
        """Get the IRIS ID of the message."""
        return self._iris_id


class _PydanticPickleMessage(_PydanticMessage):
    """Base class for Pydantic-based messages that can be serialized to IRIS."""

    def __init__(self, **data: Any):
        super().__init__(**data)
