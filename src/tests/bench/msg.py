from iop import PydanticMessage
from iop import Message
from dataclasses import dataclass

@dataclass
class MyMessage(Message):
    message : str = None

class MyPydanticMessage(PydanticMessage):
    message : str = None