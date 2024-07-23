from iop import Message
from dataclasses import dataclass

@dataclass
class MyMessage(Message):
    message : str = None