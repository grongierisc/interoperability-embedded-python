from grongier.pex import Message
from dataclasses import dataclass

@dataclass
class MyMessage(Message):
    message : str = None