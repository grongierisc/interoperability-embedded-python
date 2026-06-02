"""Unit tests for _BusinessOperation — no live IRIS instance required."""

from unittest.mock import MagicMock, patch

import pytest
from fixtures.message import SimpleMessage

from iop.components.business_operation import _BusinessOperation
from iop.messages.dispatch import dispatch_message


@pytest.fixture
def operation():
    op = _BusinessOperation()
    op.iris_handle = MagicMock()
    return op


def test_message_handling(operation):
    request = SimpleMessage(integer=1, string="test")
    with pytest.warns(RuntimeWarning, match="did not override on_message"):
        assert operation.on_message(request) is None
    assert not hasattr(operation, "OnMessage")


def test_keepalive(operation):
    assert operation.on_keepalive() is None


def test_adapter_handling():
    op = _BusinessOperation()
    mock_current = MagicMock()
    mock_partner = MagicMock()

    mock_partner._IsA.return_value = True
    mock_partner.GetModule.return_value = "some.module"
    mock_partner.GetClassname.return_value = "SomeAdapter"

    with patch("importlib.import_module") as mock_import:
        mock_module = MagicMock()
        mock_import.return_value = mock_module
        op._set_iris_handles(mock_current, mock_partner)

        assert op.iris_handle == mock_current


def test_dispatch_methods(operation):
    operation.DISPATCH = [("MessageType1", "handle_type1")]
    mock_host = MagicMock()
    mock_host.port = 0
    mock_host.enable = False

    operation._dispatch_on_init(mock_host)

    request = SimpleMessage(integer=1, string="test")
    with pytest.warns(RuntimeWarning, match="did not override on_message"):
        operation._dispatch_on_message(request)

    operation.iris_handle.dispatchOnMessage.assert_not_called()


def test_dispatch_with_custom_handlers():
    class CustomOperation(_BusinessOperation):
        def handle_simple(self, request: SimpleMessage):
            return SimpleMessage(integer=request.integer + 1, string="handled")

    op = CustomOperation()
    mock_host = MagicMock()
    mock_host.port = 0
    mock_host.enable = False
    op._dispatch_on_init(mock_host)
    op.iris_handle = MagicMock()

    request = SimpleMessage(integer=1, string="test")
    response = dispatch_message(op, request)

    assert isinstance(response, SimpleMessage)
    assert response.integer == 2
    assert response.string == "handled"


def test_dispatch_generation_ignores_inherited_stale_dispatch():
    original_dispatch = _BusinessOperation.DISPATCH
    _BusinessOperation.DISPATCH = [("some.OtherMessage", "handle_other")]

    try:

        class CustomOperation(_BusinessOperation):
            def handle_simple(self, request: SimpleMessage):
                return SimpleMessage(integer=request.integer + 1, string="handled")

        op = CustomOperation()
        mock_host = MagicMock()
        mock_host.port = 0
        mock_host.enable = False
        op._dispatch_on_init(mock_host)

        assert (
            f"{SimpleMessage.__module__}.{SimpleMessage.__name__}",
            "handle_simple",
        ) in op.DISPATCH
        assert op.DISPATCH is not _BusinessOperation.DISPATCH
    finally:
        _BusinessOperation.DISPATCH = original_dispatch
