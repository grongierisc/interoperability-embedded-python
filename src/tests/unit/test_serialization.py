"""Unit tests for serialization — no live IRIS instance required."""
from dataclasses import dataclass

import pytest

from iop import Message
from iop.messages.serialization import (
    MessageClassImportError,
    SerializationError,
    deserialize_message,
    deserialize_pickle_message,
    serialize_message,
    serialize_pickle_message,
)


@dataclass
class MyObject:
    value: str = None


class NonDataclass:
    def __init__(self, value):
        self.value = value


def test_raise_not_message():
    """serialize_message must raise SerializationError for non-Message objects."""
    msg = MyObject(value="test")
    with pytest.raises(SerializationError):
        serialize_message(msg)


@dataclass
class IrisIdMessage(Message):
    value: str = ""


def test_json_serialization_preserves_original_iris_id():
    msg = IrisIdMessage(value="test")
    msg._iris_id = "123"

    serial = serialize_message(msg)

    assert msg._iris_id == "123"
    assert "_iris_id" not in serial.json


def test_pickle_serialization_preserves_original_iris_id():
    msg = IrisIdMessage(value="test")
    msg._iris_id = "123"

    serial = serialize_pickle_message(msg)
    result = deserialize_pickle_message(serial)

    assert msg._iris_id == "123"
    assert result.get_iris_id() is None


def test_json_deserialization_class_import_error_is_import_error():
    class FakeSerial:
        classname = "missing.module.MyMsg"
        type = "String"
        json = "{}"

    with pytest.raises(MessageClassImportError) as exc:
        deserialize_message(FakeSerial())

    assert isinstance(exc.value, SerializationError)
    assert isinstance(exc.value, ImportError)
    assert "Failed to load class missing.module.MyMsg" in str(exc.value)
