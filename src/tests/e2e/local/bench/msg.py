from iop import PydanticMessage
from iop import Message
from iop import PickleMessage
from iop import PydanticPickleMessage
from dataclasses import dataclass

@dataclass
class MyMessage(Message):
    message : str = None

class MyPydanticMessage(PydanticMessage):
    message : str = None

@dataclass
class MyPickleMessage(PickleMessage):
    message : str = None

class MyPydanticPickleMessage(PydanticPickleMessage):
    message : str = None