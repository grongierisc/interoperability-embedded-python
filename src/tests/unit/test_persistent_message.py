import sys
from unittest.mock import patch

import pytest
from iris_persistence.runtime import configure_default_runtime
from iris_persistence.testing import InMemoryAdapter

from iop import Field, Model, PersistentMessage
from iop.messages import persistent as persistent_message_module
from iop.messages.dispatch import dispatch_serializer
from iop.messages.persistent import (
    deserialize_persistent_message,
    get_python_classpath,
    iris_classname_to_python_classname,
    is_persistent_message_class,
    load_python_class,
    python_classname_to_iris_classname,
    register_persistent_message_class,
)
from iop.migration.utils import _Utils


@pytest.fixture(autouse=True)
def fake_runtime():
    configure_default_runtime(InMemoryAdapter())
    persistent_message_module._PYTHON_TO_IRIS_CACHE.clear()
    persistent_message_module._IRIS_TO_PYTHON_CACHE.clear()
    persistent_message_module._IRIS_TO_PYTHON_CLASSPATH_CACHE.clear()
    persistent_message_module._IRIS_TO_PYTHON_STRICT_CACHE.clear()
    persistent_message_module._IRIS_TO_MESSAGE_CLASS_CACHE.clear()
    persistent_message_module._IRIS_PARAMETER_CACHE.clear()
    persistent_message_module._AUTO_SYNCED.clear()
    _Utils._persistent_message_registry.clear()
    yield
    _Utils._persistent_message_registry.clear()
    configure_default_runtime(None)


class NativeOrderMessage(PersistentMessage):
    OrderId: str = Field(required=True, max_length=64)
    Amount: float = 0.0


class ConventionOrderMessage(PersistentMessage):
    OrderId: str = Field(required=True, max_length=64)
    Amount: float = 0.0


def test_persistent_message_defaults():
    assert NativeOrderMessage._superclasses == "Ens.MessageBody"
    assert NativeOrderMessage._sync_mode == "extend"
    assert NativeOrderMessage._auto_sync is True


def test_model_is_public_for_nested_objects():
    class Address(Model, serial=True):
        City: str

    class CustomerMessage(PersistentMessage):
        Name: str
        ShipTo: Address

    assert Address._superclasses == "%SerialObject"
    assert CustomerMessage.__model_fields__["ShipTo"].declared_type is Address


def test_classes_registration_uses_key_as_iris_classname():
    with patch.object(NativeOrderMessage, "sync_schema", classmethod(lambda cls: None)):
        _Utils.set_classes_settings(
            {"Demo.Msg.NativeOrderMessage": NativeOrderMessage},
            root_path=".",
        )

    assert NativeOrderMessage._classname == "Demo.Msg.NativeOrderMessage"
    assert NativeOrderMessage._parameters["IOP_MESSAGE_KIND"] == "PersistentMessage"
    assert NativeOrderMessage._parameters["IOP_PYTHON_CLASS"].endswith(
        ".NativeOrderMessage"
    )
    assert NativeOrderMessage._parameters[
        "IOP_PYTHON_CLASSPATH"
    ] == get_python_classpath(NativeOrderMessage)


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


def test_deserializes_registered_native_object_from_class_cache():
    register_persistent_message_class(
        NativeOrderMessage,
        "Demo.Msg.NativeOrderMessage",
        sync_schema=False,
    )

    class FakeNative:
        OrderId = "A-2"
        Amount = 21.0

        def _Id(self):
            return "123"

    native = FakeNative()
    setattr(native, "%ClassName", lambda full=1: "Demo.Msg.NativeOrderMessage")

    with patch("iop.messages.persistent.get_iris_class_parameter") as get_parameter:
        message = deserialize_persistent_message(native)

    assert isinstance(message, NativeOrderMessage)
    assert message.OrderId == "A-2"
    get_parameter.assert_not_called()


def test_unregistered_message_uses_default_encoded_classname():
    class DefaultNameMessage(PersistentMessage):
        Value: str

    expected = python_classname_to_iris_classname(
        f"{DefaultNameMessage.__module__}.{DefaultNameMessage.__name__}"
    )

    with patch.object(DefaultNameMessage, "sync_schema", classmethod(lambda cls: None)):
        native = dispatch_serializer(DefaultNameMessage(Value="abc"))

    assert native._classname == expected
    assert DefaultNameMessage._parameters["IOP_PYTHON_CLASS"] == (
        f"{DefaultNameMessage.__module__}.{DefaultNameMessage.__name__}"
    )


def test_default_classname_convention_escapes_underscores_and_z():
    python_classname = "my_app.msgs.Order_zMessage"
    iris_classname = python_classname_to_iris_classname(python_classname)

    assert iris_classname == "myzUapp.msgs.OrderzUzzMessage"
    assert iris_classname_to_python_classname(iris_classname) == python_classname


def test_deserializes_native_object_with_default_convention_without_parameters():
    class FakeNative:
        OrderId = "A-3"
        Amount = 9.0

        def _Id(self):
            return "456"

    native = FakeNative()
    setattr(
        native,
        "%ClassName",
        lambda full=1: python_classname_to_iris_classname(
            f"{ConventionOrderMessage.__module__}.{ConventionOrderMessage.__name__}"
        ),
    )

    message = deserialize_persistent_message(native)

    assert isinstance(message, ConventionOrderMessage)
    assert message.OrderId == "A-3"
    assert message.Amount == 9.0
    assert message.get_iris_id() == "456"


def test_load_python_class_uses_classpath_on_cold_import(tmp_path):
    app_dir = tmp_path / "app"
    conflict_dir = tmp_path / "conflict"
    app_dir.mkdir()
    conflict_dir.mkdir()
    module_path = app_dir / "msg.py"
    module_path.write_text(
        "from iop import Field, PersistentMessage\n"
        "class ColdMessage(PersistentMessage):\n"
        "    Value: str = Field(required=True)\n",
        encoding="utf-8",
    )
    (conflict_dir / "msg.py").write_text(
        "class PickleMessage:\n    pass\n",
        encoding="utf-8",
    )

    sys.modules.pop("msg", None)
    while str(app_dir) in sys.path:
        sys.path.remove(str(app_dir))
    while str(conflict_dir) in sys.path:
        sys.path.remove(str(conflict_dir))
    sys.path.insert(0, str(conflict_dir))

    try:
        msg_cls = load_python_class("msg.ColdMessage", str(app_dir))

        assert msg_cls.__name__ == "ColdMessage"
        assert is_persistent_message_class(msg_cls)
        assert sys.path[0] == str(app_dir)
    finally:
        sys.modules.pop("msg", None)
        while str(app_dir) in sys.path:
            sys.path.remove(str(app_dir))
        while str(conflict_dir) in sys.path:
            sys.path.remove(str(conflict_dir))


def test_deserializes_iris_originated_message_with_class_parameters(tmp_path):
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    module_path = app_dir / "msg.py"
    module_path.write_text(
        "from iop import Field, PersistentMessage\n"
        "class ColdMessage(PersistentMessage):\n"
        "    Value: str = Field(required=True)\n",
        encoding="utf-8",
    )

    class FakeNative:
        Value = "from iris"

        def _Id(self):
            return "789"

    native = FakeNative()
    setattr(native, "%ClassName", lambda full=1: "Demo.Msg.ColdMessage")

    parameter_values = {
        ("Demo.Msg.ColdMessage", "IOP_MESSAGE_KIND"): "PersistentMessage",
        ("Demo.Msg.ColdMessage", "IOP_PYTHON_CLASS"): "msg.ColdMessage",
        ("Demo.Msg.ColdMessage", "IOP_PYTHON_CLASSPATH"): str(app_dir),
    }

    sys.modules.pop("msg", None)
    while str(app_dir) in sys.path:
        sys.path.remove(str(app_dir))

    try:
        with patch(
            "iop.messages.persistent.get_iris_class_parameter",
            side_effect=lambda iris_classname, parameter: parameter_values.get(
                (iris_classname, parameter)
            ),
        ):
            message = deserialize_persistent_message(native)

        assert message.__class__.__name__ == "ColdMessage"
        assert is_persistent_message_class(type(message))
        assert message.Value == "from iris"
        assert message.get_iris_id() == "789"
    finally:
        sys.modules.pop("msg", None)
        while str(app_dir) in sys.path:
            sys.path.remove(str(app_dir))
