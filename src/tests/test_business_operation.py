import pytest
from unittest.mock import MagicMock, patch
from iop._business_operation import _BusinessOperation
from registerFiles.message import SimpleMessage

@pytest.fixture
def operation():
    op = _BusinessOperation()
    op.iris_handle = MagicMock()
    return op

def test_message_handling(operation):
    # Test on_message
    request = SimpleMessage(integer=1, string='test')
    assert operation.on_message(request) is None
    
    # Test deprecated OnMessage
    assert operation.OnMessage(request) is None

def test_keepalive(operation):
    assert operation.on_keepalive() is None

def test_adapter_handling():
    # Test adapter setup with mock IRIS adapter
    op = _BusinessOperation()
    mock_current = MagicMock()
    mock_partner = MagicMock()
    
    # Setup mock IRIS adapter
    mock_partner._IsA.return_value = True
    mock_partner.GetModule.return_value = "some.module"
    mock_partner.GetClassname.return_value = "SomeAdapter"
    
    with patch('importlib.import_module') as mock_import:
        mock_module = MagicMock()
        mock_import.return_value = mock_module
        op._set_iris_handles(mock_current, mock_partner)
        
        assert op.iris_handle == mock_current

def test_dispatch_methods(operation):
    # Test dispatch initialization
    operation.DISPATCH = [("MessageType1", "handle_type1")]
    mock_host = MagicMock()
    
    operation._dispatch_on_init(mock_host)
    
    # Test message dispatch
    request = SimpleMessage(integer=1, string='test')
    operation._dispatch_on_message(request)
    
    # Verify internal method calls
    operation.iris_handle.dispatchOnMessage.assert_not_called()

def test_dispatch_with_custom_handlers():
    class CustomOperation(_BusinessOperation):
        def handle_simple(self, request: SimpleMessage):
            return SimpleMessage(integer=request.integer + 1, string="handled")
    
    operation = CustomOperation()
    operation._dispatch_on_init(MagicMock())
    operation.iris_handle = MagicMock()
    
    request = SimpleMessage(integer=1, string='test')
    response = operation._dispach_message(request)
    
    assert isinstance(response, SimpleMessage)
    assert response.integer == 2
    assert response.string == "handled"
