from typing import Any

from pydantic import BaseModel


class _Message:
    """Base class for JSON-serialized messages sent between components.

    Use Message for Python-only contracts that do not need native IRIS
    persistence. Subclasses must be decorated with @dataclass. App builders
    usually pair message classes with BusinessProcess or BusinessOperation
    handlers; see
    docs/cookbooks/add-business-process.md and
    docs/cookbooks/add-business-operation.md.
    """

    _iris_id: str | None = None

    def get_iris_id(self) -> str | None:
        """Get the IRIS ID of the message."""
        return self._iris_id


class _PickleMessage(_Message):
    """Base class for pickle-serialized messages sent between components.

    Prefer Message or PydanticMessage for new application contracts. Use
    PickleMessage only when a Python-only payload cannot be represented cleanly
    as JSON-compatible fields.
    """

    pass


class _PydanticMessage(BaseModel):
    """Base class for Pydantic-based messages that can be serialized to IRIS.

    Use PydanticMessage for Python-only contracts that benefit from Pydantic
    validation. Do not decorate PydanticMessage classes with @dataclass and do
    not register these classes in CLASSES; see docs/getting-started/register-component.md.
    """

    _iris_id: str | None = None

    def __init__(self, **data: Any):
        super().__init__(**data)

    def get_iris_id(self) -> str | None:
        """Get the IRIS ID of the message."""
        return self._iris_id


class _PydanticPickleMessage(_PydanticMessage):
    """Base class for Pydantic-based messages serialized through pickle.

    Prefer PydanticMessage unless the payload must preserve Python-only object
    shapes that JSON serialization cannot represent.
    """

    def __init__(self, **data: Any):
        super().__init__(**data)
