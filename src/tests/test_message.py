import iris

from iop import Message, PickleMessage, PydanticMessage, PydanticPickleMessage
from iop._dispatch import dispatch_serializer, dispatch_deserializer

from dataclasses import dataclass

@dataclass
class SimpleMessage(Message):
    """A simple message class for testing"""

    integer: int
    string: str

@dataclass
class SimplePickleMessage(PickleMessage):
    """A simple pickle message class for testing"""

    integer: int
    string: str

class SimplePydanticMessage(PydanticMessage):
    """A simple Pydantic message class for testing"""

    integer: int
    string: str

class SimplePydanticPickleMessage(PydanticPickleMessage):
    """A simple Pydantic pickle message class for testing"""

    integer: int
    string: str

import pytest

def test_iop_message_set_json():
    # test set_json
    iop_message = iris.cls('IOP.Message')._New()
    iop_message.json = 'test'
    assert iop_message.jstr.Read() == 'test'
    assert iop_message.type == 'String'
    assert iop_message.jsonString == 'test'
    assert iop_message.json == 'test'

@pytest.mark.parametrize("message_class", [
    SimpleMessage,
    SimplePickleMessage,
    SimplePydanticMessage,
    SimplePydanticPickleMessage
]
)
def test_get_iris_id(message_class):
    message = message_class(integer=42, string='test')
    assert message.get_iris_id() is None

    serialized_message = dispatch_serializer(message)
    serialized_message._Save()
    deserialized_message = dispatch_deserializer(serialized_message)

    assert deserialized_message.get_iris_id() is not None

