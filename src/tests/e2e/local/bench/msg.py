from dataclasses import dataclass

from iop import Field
from iop import Message
from iop import PersistentMessage
from iop import PickleMessage
from iop import PydanticMessage
from iop import PydanticPickleMessage


@dataclass
class MyMessage(Message):
    message: str = None


class MyPydanticMessage(PydanticMessage):
    message: str = None


@dataclass
class MyPickleMessage(PickleMessage):
    message: str = None


class MyPydanticPickleMessage(PydanticPickleMessage):
    message: str = None


class MyPersistentMessage(PersistentMessage):
    message: str = Field(default="")

    class Meta:
        classname = "Bench.Msg.MyPersistentMessage"
