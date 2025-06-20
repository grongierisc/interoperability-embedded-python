from typing import Any, Optional

from pydantic import BaseModel

class _Message:
    """ The abstract class that is the superclass for persistent messages sent from one component to another.
    This class has no properties or methods. Users subclass Message and add properties.
    The IOP framework provides the persistence to objects derived from the Message class.
    """
    _iris_id: Optional[str] = None
    
    def get_iris_id(self) -> Optional[str]:
        """Get the IRIS ID of the message."""
        return self._iris_id

class _PickleMessage(_Message):
    """ The abstract class that is the superclass for persistent messages sent from one component to another.
    This class has no properties or methods. Users subclass Message and add properties.
    The IOP framework provides the persistence to objects derived from the Message class.
    """
    pass

class _PydanticMessage(BaseModel):
    """Base class for Pydantic-based messages that can be serialized to IRIS."""
    
    _iris_id: Optional[str] = None

    def __init__(self, **data: Any):
        super().__init__(**data)

    def get_iris_id(self) -> Optional[str]:
        """Get the IRIS ID of the message."""
        return self._iris_id

class _PydanticPickleMessage(_PydanticMessage):
    """Base class for Pydantic-based messages that can be serialized to IRIS."""

    def __init__(self, **data: Any):
        super().__init__(**data)

