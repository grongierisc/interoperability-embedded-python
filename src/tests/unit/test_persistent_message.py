from unittest.mock import patch

import pytest
from iris_persistence.runtime import configure_default_runtime
from iris_persistence.testing import InMemoryAdapter

from iop import Field, PersistentMessage
from iop._dispatch import dispatch_serializer
from iop._persistent_message import (
    deserialize_persistent_message,
    register_persistent_message_class,
)
from iop._utils import _Utils


@pytest.fixture(autouse=True)
def fake_runtime():
    configure_default_runtime(InMemoryAdapter())
    yield
    configure_default_runtime(None)


class NativeOrderMessage(PersistentMessage):
    OrderId: str = Field(required=True, max_length=64)
    Amount: float = 0.0


def test_persistent_message_defaults():
    assert NativeOrderMessage._superclasses == "Ens.MessageBody"
    assert NativeOrderMessage._sync_mode == "extend"
    assert NativeOrderMessage._auto_sync is True


def test_classes_registration_uses_key_as_iris_classname():
    with patch.object(NativeOrderMessage, "sync_schema", classmethod(lambda cls: None)):
        with patch("iop._persistent_message._register_mapping_in_iris") as mock_registry:
            _Utils.set_classes_settings(
                {"Demo.Msg.NativeOrderMessage": NativeOrderMessage},
                root_path=".",
            )

    assert NativeOrderMessage._classname == "Demo.Msg.NativeOrderMessage"
    assert NativeOrderMessage._parameters["IOP_MESSAGE_KIND"] == "PersistentMessage"
    assert NativeOrderMessage._parameters["IOP_PYTHON_CLASS"].endswith(".NativeOrderMessage")
    mock_registry.assert_called_once()


def test_explicit_meta_classname_conflict_raises():
    class ConflictingMessage(PersistentMessage):
        Value: str

        class Meta:
            classname = "Demo.Msg.Expected"

    with pytest.raises(ValueError, match="Meta.classname"):
        register_persistent_message_class(
            ConflictingMessage,
            "Demo.Msg.Actual",
            sync_schema=False,
        )


def test_dispatch_serializes_to_native_iris_object():
    with patch.object(NativeOrderMessage, "sync_schema", classmethod(lambda cls: None)):
        with patch("iop._persistent_message._register_mapping_in_iris"):
            register_persistent_message_class(
                NativeOrderMessage,
                "Demo.Msg.NativeOrderMessage",
            )

        native = dispatch_serializer(NativeOrderMessage(OrderId="A-1", Amount=12.5))

    assert native._classname == "Demo.Msg.NativeOrderMessage"
    assert native.OrderId == "A-1"
    assert native.Amount == 12.5


def test_deserializes_registered_native_iris_object():
    with patch.object(NativeOrderMessage, "sync_schema", classmethod(lambda cls: None)):
        with patch("iop._persistent_message._register_mapping_in_iris"):
            register_persistent_message_class(
                NativeOrderMessage,
                "Demo.Msg.NativeOrderMessage",
            )

    class FakeNative:
        OrderId = "A-2"
        Amount = 21.0

        def _Id(self):
            return "123"

    native = FakeNative()
    setattr(native, "%ClassName", lambda full=1: "Demo.Msg.NativeOrderMessage")

    message = deserialize_persistent_message(native)

    assert isinstance(message, NativeOrderMessage)
    assert message.OrderId == "A-2"
    assert message.Amount == 21.0
    assert message.get_iris_id() == "123"
