"""Unit tests for serialization — no live IRIS instance required."""
import pytest
from dataclasses import dataclass

from iop.messages.serialization import (
    SerializationError,
    deserialize_pickle_message,
    serialize_message,
    serialize_pickle_message,
)
from iop import Message


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
