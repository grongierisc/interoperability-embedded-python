"""Unit tests for _BusinessOperation — no live IRIS instance required."""
import pytest
from unittest.mock import MagicMock, patch

from iop._business_operation import _BusinessOperation
from iop._dispatch import dispach_message
from fixtures.message import SimpleMessage


@pytest.fixture
def operation():
    op = _BusinessOperation()
    op.iris_handle = MagicMock()
    return op


def test_message_handling(operation):
    request = SimpleMessage(integer=1, string='test')
    assert operation.on_message(request) is None
    assert operation.OnMessage(request) is None


def test_keepalive(operation):
    assert operation.on_keepalive() is None


def test_adapter_handling():
    op = _BusinessOperation()
    mock_current = MagicMock()
    mock_partner = MagicMock()

    mock_partner._IsA.return_value = True
    mock_partner.GetModule.return_value = "some.module"
    mock_partner.GetClassname.return_value = "SomeAdapter"

    with patch('importlib.import_module') as mock_import:
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

    request = SimpleMessage(integer=1, string='test')
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

    request = SimpleMessage(integer=1, string='test')
    response = dispach_message(op, request)

    assert isinstance(response, SimpleMessage)
    assert response.integer == 2
    assert response.string == "handled"
