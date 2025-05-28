from typing import Any

from pydantic import BaseModel

class _Message:
    """ The abstract class that is the superclass for persistent messages sent from one component to another.
    This class has no properties or methods. Users subclass Message and add properties.
    The IOP framework provides the persistence to objects derived from the Message class.
    """
    pass

class _PickleMessage:
    """ The abstract class that is the superclass for persistent messages sent from one component to another.
    This class has no properties or methods. Users subclass Message and add properties.
    The IOP framework provides the persistence to objects derived from the Message class.
    """
    pass

class _PydanticMessage(BaseModel):
    """Base class for Pydantic-based messages that can be serialized to IRIS."""
    
    def __init__(self, **data: Any):
        super().__init__(**data)

class _PydanticPickleMessage(BaseModel):
    """Base class for Pydantic-based messages that can be serialized to IRIS."""
    
    def __init__(self, **data: Any):
        super().__init__(**data)