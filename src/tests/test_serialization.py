import datetime
import decimal
from typing import Optional
import uuid
from dataclasses import dataclass

import pytest
import iris

from iop._serialization import (
    SerializationError,
    serialize_message,
    deserialize_message,
    serialize_pickle_message,
    deserialize_pickle_message,
)

from iop import Message

class NonDataclass:
    def __init__(self, value):
        self.value = value

@dataclass
class Empty(Message):
    pass

@dataclass
class Object:
    value: str

@dataclass
class FullMessge(Message):
    """Full message class with various fields."""
    text: str
    dikt: dict
    text_json: str
    obj: Object
    number: int
    date: datetime.date
    time: datetime.time
    dt: datetime.datetime
    dec: decimal.Decimal
    uid: uuid.UUID
    data: bytes
    items: list  # Changed from df to a simple list
    list_obj: list[Object] = None
    dict_obj: dict[str, Object] = None
    optional_obj: Optional[Object] = None

@dataclass
class MyObject:
    value: str = None
    foo: int = None
    bar: float = 3.14

@dataclass
class Msg(Message):
    text: str
    number: int
    my_obj: MyObject

def test_empty_serialization():
    # Create an empty message
    msg = Empty()
    msg.foo = 42
    msg.bar = "hello"

    # Test serialization
    serial = serialize_message(msg)
    assert type(serial).__module__.startswith('iris') and serial._IsA("IOP.Message")
    assert serial.classname == f"{Empty.__module__}.{Empty.__name__}"
    
    # Test deserialization
    result = deserialize_message(serial)
    assert isinstance(result, Empty)
    assert result.foo == msg.foo
    assert result.bar == msg.bar

def test_message_serialization():
    msg = Msg(text="hello", number=42, my_obj=None)

    my_obj = MyObject(value="test", foo=None)

    # hack my_obj as a dict
    msg.my_obj = {}
    msg.my_obj['value'] = "test"
    msg.my_obj['foo'] = None
    msg.my_obj['other'] = 3.14

    # Test serialization
    serial = serialize_message(msg)
    assert type(serial).__module__.startswith('iris') and serial._IsA("IOP.Message")
    assert serial.classname == f"{Msg.__module__}.{Msg.__name__}"

    # Test deserialization
    result = deserialize_message(serial)
    assert isinstance(result, Msg)
    assert result.text == msg.text
    assert result.number == msg.number
    assert result.my_obj == my_obj

def test_raise_not_message():
    # Create a message with an invalid object
    msg = MyObject(value="test", foo=None)

    # Test serialization
    with pytest.raises(SerializationError):
        serialize_message(msg)


def test_unexpexted_obj_serialization():
    # Create an invalid message
    msg = Msg(text="hello", number=42, my_obj=None)
    msg.my_obj = NonDataclass(value="test")

    # Test serialization
    serial = serialize_message(msg)
    assert type(serial).__module__.startswith('iris') and serial._IsA("IOP.Message")
    assert serial.classname == f"{Msg.__module__}.{Msg.__name__}"

    # Test deserialization
    result = deserialize_message(serial)
    assert isinstance(result, Msg)
    assert result.text == msg.text
    assert result.number == msg.number
    assert result.my_obj.value == msg.my_obj.value


def test_unexpected_fields():
    # Create a message with unexpected fields
    msg = Msg(text="hello", number=42, my_obj=None)
    msg.unexpected_field = "unexpected"

    my_obj = MyObject(value="test", foo=None)
    my_obj.unexpected_field = "unexpected"
    msg.my_obj = my_obj

    # Test serialization
    serial = serialize_message(msg)
    assert type(serial).__module__.startswith('iris') and serial._IsA("IOP.Message")
    assert serial.classname == f"{Msg.__module__}.{Msg.__name__}"

    # Test deserialization
    result = deserialize_message(serial)
    assert isinstance(result, Msg)
    assert result.text == msg.text
    assert result.number == msg.number
    assert result.unexpected_field == msg.unexpected_field
    assert result.my_obj == my_obj


def test_json_serialization():
    # Create test data
    test_items = [{'col1': 1, 'col2': 'a'}, {'col1': 2, 'col2': 'b'}]  # Simple list of dicts instead of DataFrame
    test_uuid = uuid.uuid4()
    test_bytes = b'hello world\x04'
    
    msg = FullMessge(
        text="test",
        dikt={'key': 'value'},
        text_json="{\"key\": \"value\"}",
        obj=Object(value="test"),
        number=42,
        date=datetime.date(2023, 1, 1),
        time=datetime.time(12, 0),
        dt=datetime.datetime(2023, 1, 1, 12, 0),
        dec=decimal.Decimal("3.14"),
        uid=test_uuid,
        data=test_bytes,
        items=test_items
    )
    
    # Test serialization
    serial = serialize_message(msg)
    assert type(serial).__module__.startswith('iris') and serial._IsA("IOP.Message")
    assert serial.classname == f"{FullMessge.__module__}.{FullMessge.__name__}"
    
    # Test deserialization
    result = deserialize_message(serial)
    assert isinstance(result, FullMessge)
    assert result.text == msg.text
    assert result.dikt == msg.dikt
    assert result.text_json == msg.text_json
    assert result.obj == msg.obj
    assert result.number == msg.number
    assert result.date == msg.date
    assert result.time == msg.time
    assert result.dt == msg.dt
    assert result.dec == msg.dec
    assert result.uid == msg.uid
    assert result.data == msg.data
    assert result.items == msg.items

def test_pickle_serialization():
    msg = FullMessge(
        text="test",
        dikt={'key': 'value'},
        text_json="{\"key\": \"value\"}",
        obj=Object(value="test"),
        number=42,
        date=datetime.date(2023, 1, 1),
        time=datetime.time(12, 0),
        dt=datetime.datetime(2023, 1, 1, 12, 0),
        dec=decimal.Decimal("3.14"),
        uid=uuid.uuid4(),
        data=b'hello world',
        items=[{'col1': 1, 'col2': 'a'}, {'col1': 2, 'col2': 'b'}],
        list_obj=[Object(value="item1"), Object(value="item2")],
        dict_obj={'key1': Object(value="item1"), 'key2': Object(value="item2")},
        optional_obj=Object(value="optional")
    )
    
    # Test serialization
    serial = serialize_pickle_message(msg)
    assert type(serial).__module__.startswith('iris') and serial._IsA("IOP.PickleMessage")
    assert serial.classname == f"{FullMessge.__module__}.{FullMessge.__name__}"
    
    # Test deserialization
    result = deserialize_pickle_message(serial)
    assert isinstance(result, FullMessge)
    assert result.text == msg.text
    assert result.dikt == msg.dikt
    assert result.text_json == msg.text_json
    assert result.obj == msg.obj
    assert result.number == msg.number
    assert result.date == msg.date
    assert result.time == msg.time
    assert result.dt == msg.dt
    assert result.dec == msg.dec
    assert result.uid == msg.uid
    assert result.data == msg.data
    assert result.items == msg.items
    assert result.list_obj == msg.list_obj
    assert result.dict_obj == msg.dict_obj
    assert result.optional_obj == msg.optional_obj

def test_invalid_message_deserialization():
    # Create an invalid message without classname
    msg = iris.cls('IOP.Message')._New()
    msg.classname = None
    msg.json = "{}"
    
    with pytest.raises(SerializationError, match="JSON message malformed, must include classname"):
        deserialize_message(msg)
    
    # Test invalid module
    msg.classname = "invalid.module.Class"
    with pytest.raises(SerializationError, match="Failed to load class invalid.module.Class: No module named 'invalid'"):
        deserialize_message(msg)
