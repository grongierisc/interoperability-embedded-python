import datetime
import decimal
import uuid
from typing import List, Optional

import pytest
from pydantic import BaseModel

from iop._message import _PydanticMessage as PydanticMessage
from iop._serialization import (
    serialize_message,
    deserialize_message,
    serialize_pickle_message,
    deserialize_pickle_message,
)

class SimpleModel(BaseModel):
    value: str

class FullPydanticMessage(PydanticMessage):
    text: str
    dikt: dict
    text_json: str
    obj: SimpleModel
    number: int
    date: datetime.date
    time: datetime.time
    dt: datetime.datetime
    dec: decimal.Decimal
    uid: uuid.UUID
    data: bytes
    items: List[dict]
    optional_field: Optional[str] = None

def test_pydantic_json_serialization():
    # Create test data
    test_items = [{'col1': 1, 'col2': 'a'}, {'col1': 2, 'col2': 'b'}]
    test_uuid = uuid.uuid4()
    test_bytes = b'hello world'
    
    msg = FullPydanticMessage(
        text="test",
        dikt={'key': 'value'},
        text_json="{\"key\": \"value\"}",
        obj=SimpleModel(value="test"),
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
    assert serial._IsA("IOP.Message")
    assert serial.classname == f"{FullPydanticMessage.__module__}.{FullPydanticMessage.__name__}"
    
    # Test deserialization
    result = deserialize_message(serial)
    assert isinstance(result, FullPydanticMessage)
    assert result.model_dump() == msg.model_dump()

def test_pydantic_pickle_serialization():
    msg = FullPydanticMessage(
        text="test",
        dikt={'key': 'value'},
        text_json="{\"key\": \"value\"}",
        obj=SimpleModel(value="test"),
        number=42,
        date=datetime.date(2023, 1, 1),
        time=datetime.time(12, 0),
        dt=datetime.datetime(2023, 1, 1, 12, 0),
        dec=decimal.Decimal("3.14"),
        uid=uuid.uuid4(),
        data=b'hello world',
        items=[{'col1': 1, 'col2': 'a'}]
    )
    
    # Test serialization
    serial = serialize_pickle_message(msg)
    assert serial._IsA("IOP.PickleMessage")
    assert serial.classname == f"{FullPydanticMessage.__module__}.{FullPydanticMessage.__name__}"
    
    # Test deserialization
    result = deserialize_pickle_message(serial)
    assert isinstance(result, FullPydanticMessage)
    assert result.model_dump() == msg.model_dump()

def test_optional_fields():
    # Test with optional field set
    msg1 = FullPydanticMessage(
        text="test",
        dikt={},
        text_json="{}",
        obj=SimpleModel(value="test"),
        number=42,
        date=datetime.date(2023, 1, 1),
        time=datetime.time(12, 0),
        dt=datetime.datetime(2023, 1, 1, 12, 0),
        dec=decimal.Decimal("3.14"),
        uid=uuid.uuid4(),
        data=b'hello',
        items=[],
        optional_field="present"
    )
    
    # Test with optional field not set
    msg2 = FullPydanticMessage(
        text="test",
        dikt={},
        text_json="{}",
        obj=SimpleModel(value="test"),
        number=42,
        date=datetime.date(2023, 1, 1),
        time=datetime.time(12, 0),
        dt=datetime.datetime(2023, 1, 1, 12, 0),
        dec=decimal.Decimal("3.14"),
        uid=uuid.uuid4(),
        data=b'hello',
        items=[]
    )
    
    # Test both serialization methods for each message
    for msg in [msg1, msg2]:
        for serialize_fn, deserialize_fn in [
            (serialize_message, deserialize_message),
            (serialize_pickle_message, deserialize_pickle_message)
        ]:
            serial = serialize_fn(msg)
            result = deserialize_fn(serial)
            assert isinstance(result, FullPydanticMessage)
            assert result.model_dump() == msg.model_dump()
