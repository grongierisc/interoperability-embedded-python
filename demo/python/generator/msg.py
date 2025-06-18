from iop import Message
from dataclasses import dataclass

@dataclass
class MyGenerator(Message):
    """Base message to initialize generator function"""
    my_string: str

@dataclass
class MyGeneratorResponse(Message):
    """Base message to return generator function response"""
    my_other_string: str
