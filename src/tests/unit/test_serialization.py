"""Unit tests for serialization — no live IRIS instance required."""
import pytest
from dataclasses import dataclass

from iop._serialization import SerializationError, serialize_message
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
