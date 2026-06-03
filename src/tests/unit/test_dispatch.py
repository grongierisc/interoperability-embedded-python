import datetime
import decimal
import uuid
from dataclasses import dataclass

import pytest

from iop.messages.base import _Message as Message
from iop.messages.base import _PydanticMessage as PydanticMessage
from iop.messages.dispatch import (
    create_dispatch,
    dispatch_deserializer,
    dispatch_message,
    dispatch_serializer,
    handler,
)
from iop.messages.serialization import (
    dataclass_from_dict,
    deserialize_message,
    deserialize_pickle_message,
    serialize_message,
    serialize_pickle_message,
)


class SimpleModel(PydanticMessage):
    text: str
    number: int

class ComplexModel(PydanticMessage):
    text: str
    dikt: dict
    number: int
    date: datetime.date
    dec: decimal.Decimal
    uid: uuid.UUID
    data: bytes


@dataclass 
class MessageTest(Message):
    text: str
    number: int
    
@dataclass
class ComplexMessage(Message):
    text: str
    dikt: dict
    number: int
    date: datetime.date
    dec: decimal.Decimal
    uid: uuid.UUID
    data: bytes

def test_simple_message_serialization():
    msg = SimpleModel(text="test", number=42)
    
    # Test serialization
    serial = serialize_message(msg)
    assert type(serial).__module__.startswith('iris')
    assert serial._IsA("IOP.Message")
    assert serial.classname == f"{SimpleModel.__module__}.{SimpleModel.__name__}"
    
    # Test deserialization
    result = deserialize_message(serial)
    assert isinstance(result, SimpleModel)
    assert result.text == msg.text
    assert result.number == msg.number

def test_simple_message_serialization_with_extra():
    msg = MessageTest(text="test", number=42)
    msg.extra_field = "extra"
    
    # Test serialization
    serial = serialize_message(msg)
    assert type(serial).__module__.startswith('iris')
    assert serial._IsA("IOP.Message")
    assert serial.classname == f"{MessageTest.__module__}.{MessageTest.__name__}"
    
    # Test deserialization
    result = deserialize_message(serial)
    assert isinstance(result, MessageTest)
    assert result.text == msg.text
    assert result.number == msg.number
    assert result.extra_field == msg.extra_field

def test_message_serialization():
    msg = MessageTest(text="test", number=42)
    
    # Test serialization
    serial = serialize_message(msg)
    assert type(serial).__module__.startswith('iris')
    assert serial._IsA("IOP.Message")
    assert serial.classname == f"{MessageTest.__module__}.{MessageTest.__name__}"
    
    # Test deserialization
    result = deserialize_message(serial)
    assert isinstance(result, MessageTest)
    assert result.text == msg.text
    assert result.number == msg.number

def test_message_serialization_wrong_type():
    msg = MessageTest(text="test", number={"key": "value"})
    
    # Test serialization
    serial = serialize_message(msg)
    assert type(serial).__module__.startswith('iris')
    assert serial._IsA("IOP.Message")
    assert serial.classname == f"{MessageTest.__module__}.{MessageTest.__name__}"
    
    # Test deserialization
    result = deserialize_message(serial)
    assert isinstance(result, MessageTest)
    assert result.text == msg.text
    assert result.number == msg.number

def test_pickle_message_serialization():
    msg = SimpleModel(text="test", number=42)
    
    # Test serialization
    serial = serialize_pickle_message(msg)
    assert type(serial).__module__.startswith('iris')
    assert serial._IsA("IOP.PickleMessage")
    
    # Test deserialization
    result = deserialize_pickle_message(serial)
    assert isinstance(result, SimpleModel)
    assert result.text == msg.text
    assert result.number == msg.number

def test_pickle_serialization():
    msg = MessageTest(text="test", number=42)
    
    # Test serialization 
    serial = serialize_pickle_message(msg)
    assert type(serial).__module__.startswith('iris')
    assert serial._IsA("IOP.PickleMessage")
    
    # Test deserialization
    result = deserialize_pickle_message(serial)
    assert isinstance(result, MessageTest)
    assert result.text == msg.text
    assert result.number == msg.number

def test_complex_model_serialization():
    test_uuid = uuid.uuid4()
    msg = ComplexModel(
        text="test",
        dikt={'key': 'value'},
        number=42,
        date=datetime.date(2023, 1, 1),
        dec=decimal.Decimal("3.14"),
        uid=test_uuid,
        data=b'test'
    )

    # Test dispatch serializer
    serial = dispatch_serializer(msg)
    assert type(serial).__module__.startswith('iris')
    
    # Test dispatch deserializer
    result = dispatch_deserializer(serial)
    assert isinstance(result, ComplexModel)
    assert result.text == msg.text
    assert result.dikt == msg.dikt
    assert result.number == msg.number
    assert result.date == msg.date
    assert result.dec == msg.dec
    assert result.uid == msg.uid
    assert result.data == msg.data

def test_complex_message_serialization():
    test_uuid = uuid.uuid4()
    msg = ComplexMessage(
        text="test",
        dikt={'key': 'value'},
        number=42,
        date=datetime.date(2023, 1, 1),
        dec=decimal.Decimal("3.14"),
        uid=test_uuid,
        data=b'test'
    )

    # Test dispatch serializer
    serial = dispatch_serializer(msg)
    assert type(serial).__module__.startswith('iris')
    
    # Test dispatch deserializer
    result = dispatch_deserializer(serial)
    assert isinstance(result, ComplexMessage)
    assert result.text == msg.text
    assert result.dikt == msg.dikt
    assert result.number == msg.number
    assert result.date == msg.date
    assert result.dec == msg.dec
    assert result.uid == msg.uid
    assert result.data == msg.data

def test_dataclass_from_dict():
    data = {
        'text': 'test',
        'number': 42,
        'extra_field': 'extra'
    }
    
    result = dataclass_from_dict(MessageTest, data)
    assert isinstance(result, MessageTest)
    assert result.text == 'test'
    assert result.number == 42
    assert result.extra_field == 'extra'

def test_dispatch_edge_cases():
    # Test None values
    assert dispatch_serializer(None) is None
    assert dispatch_deserializer(None) is None
    
    # Test empty string
    assert dispatch_serializer("") == ""
    
    # Test invalid message type
    with pytest.raises(TypeError):
        dispatch_serializer("invalid")


def test_handler_decorator_has_priority_over_typed_method():
    logs = []

    class Host:
        def on_message(self, request):
            return "fallback"

        @handler(MessageTest)
        def _explicit(self, request):
            return "explicit"

        def implicit(self, request: MessageTest):
            return "implicit"

        def log_warning(self, message):
            logs.append(message)

    host = Host()
    create_dispatch(host)

    assert host.DISPATCH == [
        (f"{MessageTest.__module__}.{MessageTest.__name__}", "_explicit")
    ]
    assert dispatch_message(host, MessageTest(text="test", number=1)) == "explicit"
    assert len(logs) == 1
    assert "keeping _explicit from @handler" in logs[0]
    assert "discarding implicit from typed method" in logs[0]


def test_duplicate_legacy_mappings_log_discarded_handler():
    logs = []

    class Host:
        def on_message(self, request):
            return "fallback"

        def first(self, request: MessageTest):
            return "first"

        def second(self, request: MessageTest):
            return "second"

        def log_warning(self, message):
            logs.append(message)

    host = Host()
    create_dispatch(host)

    assert host.DISPATCH == [
        (f"{MessageTest.__module__}.{MessageTest.__name__}", "second")
    ]
    assert dispatch_message(host, MessageTest(text="test", number=1)) == "second"
    assert len(logs) == 1
    assert "keeping second from typed method" in logs[0]
    assert "discarding first from typed method" in logs[0]


def test_duplicate_declared_mappings_log_discarded_handler():
    message = f"{MessageTest.__module__}.{MessageTest.__name__}"
    logs = []

    class Host:
        DISPATCH = [(message, "first"), (message, "second")]

        def on_message(self, request):
            return "fallback"

        def first(self, request):
            return "first"

        def second(self, request):
            return "second"

        def log_warning(self, message):
            logs.append(message)

    host = Host()
    create_dispatch(host)

    assert host.DISPATCH == [(message, "second")]
    assert dispatch_message(host, MessageTest(text="test", number=1)) == "second"
    assert len(logs) == 1
    assert "keeping second from DISPATCH" in logs[0]
    assert "discarding first from DISPATCH" in logs[0]


def test_handler_is_exported_from_iop():
    from iop import handler as exported_handler

    assert exported_handler is handler
