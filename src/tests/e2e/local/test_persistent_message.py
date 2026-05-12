"""E2E (local IRIS) tests for PersistentMessage native message bodies."""

from unittest.mock import MagicMock

from iop import Field, PersistentMessage
from iop import _persistent_message as persistent_message_module
from iop._business_operation import _BusinessOperation
from iop._dispatch import dispatch_deserializer, dispatch_serializer
from iop._persistent_message import register_persistent_message_class
from iop._utils import _Utils


class NativeOrderMessage(PersistentMessage):
    OrderId: str = Field(required=True, max_length=64)
    Amount: float = 0.0


def _clear_persistent_message_runtime_caches():
    persistent_message_module._PYTHON_TO_IRIS_CACHE.clear()
    persistent_message_module._IRIS_TO_PYTHON_CACHE.clear()
    persistent_message_module._IRIS_TO_PYTHON_CLASSPATH_CACHE.clear()
    persistent_message_module._IRIS_TO_PYTHON_STRICT_CACHE.clear()
    persistent_message_module._IRIS_PARAMETER_CACHE.clear()


def test_persistent_message_native_round_trip():
    _Utils.setup()
    register_persistent_message_class(
        NativeOrderMessage,
        "UnitTest.NativeOrderMessage",
    )

    native = dispatch_serializer(NativeOrderMessage(OrderId="E2E-1", Amount=10.0))

    assert native._IsA("UnitTest.NativeOrderMessage")
    assert native.OrderId == "E2E-1"
    assert native.Amount == 10.0

    _clear_persistent_message_runtime_caches()
    restored = dispatch_deserializer(native)

    assert isinstance(restored, NativeOrderMessage)
    assert restored.OrderId == "E2E-1"
    assert restored.Amount == 10.0


def test_persistent_message_typed_dispatch():
    _Utils.setup()
    register_persistent_message_class(
        NativeOrderMessage,
        "UnitTest.NativeOrderMessage",
    )

    class CustomOperation(_BusinessOperation):
        def handle_native_order(self, request: NativeOrderMessage):
            return NativeOrderMessage(
                OrderId=request.OrderId,
                Amount=request.Amount + 1,
            )

    operation = CustomOperation()
    mock_host = MagicMock()
    mock_host.port = 0
    mock_host.enable = False
    operation._dispatch_on_init(mock_host)

    request = dispatch_serializer(NativeOrderMessage(OrderId="E2E-2", Amount=41.0))
    response = operation._dispatch_on_message(request)

    assert response._IsA("UnitTest.NativeOrderMessage")
    assert response.OrderId == "E2E-2"
    assert response.Amount == 42.0
