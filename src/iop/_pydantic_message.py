
from typing import Any
from pydantic import BaseModel

class _PydanticMessage(BaseModel):
    """Base class for Pydantic-based messages that can be serialized to IRIS."""
    
    def __init__(self, **data: Any):
        super().__init__(**data)