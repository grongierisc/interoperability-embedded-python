import pytest
from unittest.mock import MagicMock, patch
from iop._business_service import _BusinessService
from registerFiles.message import SimpleMessage

@pytest.fixture
def service():
    svc = _BusinessService()
    svc.iris_handle = MagicMock()
    return svc

def test_process_input(service):
    # Test on_process_input
    message = SimpleMessage(integer=1, string='test')
    assert service.on_process_input(message) is None
    
    # Test deprecated OnProcessInput
    assert service.OnProcessInput(message) is None

def test_adapter_handling():
    # Test adapter setup with mock IRIS adapter
    svc = _BusinessService()
    mock_current = MagicMock()
    mock_partner = MagicMock()
    
    # Setup mock IRIS adapter
    mock_partner._IsA.return_value = True
    mock_partner.GetModule.return_value = "some.module"
    mock_partner.GetClassname.return_value = "SomeAdapter"
    
    with patch('importlib.import_module') as mock_import:
        mock_module = MagicMock()
        mock_import.return_value = mock_module
        svc._set_iris_handles(mock_current, mock_partner)
        
        assert svc.iris_handle == mock_current
        assert svc.Adapter is not None
        assert svc.adapter is not None

def test_dispatch_on_process_input(service):
    message = SimpleMessage(integer=1, string='test')
    service._dispatch_on_process_input(message)
    
    # Verify the message was processed
    service.iris_handle.dispatchOnProcessInput.assert_not_called()

def test_custom_service():
    class CustomService(_BusinessService):
        def on_process_input(self, message):
            return SimpleMessage(integer=message.integer * 2, string=f"processed_{message.string}")
    
    service = CustomService()
    service.iris_handle = MagicMock()
    
    input_msg = SimpleMessage(integer=5, string='test')
    result = service.on_process_input(input_msg)
    
    assert isinstance(result, SimpleMessage)
    assert result.integer == 10
    assert result.string == "processed_test"

def test_wait_for_next_call_interval(service):
    assert service._wait_for_next_call_interval is False
