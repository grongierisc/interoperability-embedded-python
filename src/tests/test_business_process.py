import pytest
from unittest.mock import MagicMock, patch
from iop._business_process import _BusinessProcess
from iop._dispatch import dispatch_serializer
from registerFilesIop.message import SimpleMessage, PickledMessage, FullMessage

@pytest.fixture
def process():
    proc = _BusinessProcess()
    proc.iris_handle = MagicMock()
    return proc

def test_message_handling(process):
    # Test on_message
    request = SimpleMessage(integer=1, string='test')
    assert process.on_message(request) is None
    
    # Test on_request
    assert process.on_request(request) is None
    
    # Test on_response
    response = SimpleMessage(integer=2, string='response')
    call_request = SimpleMessage(integer=3, string='call_request')
    call_response = SimpleMessage(integer=4, string='call_response')
    completion_key = "test_key"
    
    assert process.on_response(
        request, response, call_request, call_response, completion_key
    ) == response
    
    # Test on_complete
    assert process.on_complete(request, response) == response

def test_async_operations(process):
    # Test send_request_async
    target = "target_service"
    request = SimpleMessage(integer=1, string='test')
    process.send_request_async(target, request)
    process.iris_handle.dispatchSendRequestAsync.assert_called_once()

    # Test set_timer
    timeout = 1000
    completion_key = "timer_key"
    process.set_timer(timeout, completion_key)
    process.iris_handle.dispatchSetTimer.assert_called_once_with(
        timeout, completion_key
    )

def test_persistent_properties():
    # Test persistent property handling
    class ProcessWithProperties(_BusinessProcess):
        PERSISTENT_PROPERTY_LIST = ["test_prop"]
        def __init__(self):
            super().__init__()
            self.test_prop = "test_value"

    process = ProcessWithProperties()
    mock_host = MagicMock()
    
    # Test save properties
    process._save_persistent_properties(mock_host)
    mock_host.setPersistentProperty.assert_called_once_with("test_prop", "test_value")
    
    # Test restore properties
    mock_host.getPersistentProperty.return_value = "restored_value"
    process._restore_persistent_properties(mock_host)
    assert process.test_prop == "restored_value"

def test_dispatch_methods(process):
    mock_host = MagicMock()
    request = SimpleMessage(integer=1, string='test')
    response = SimpleMessage(integer=2, string='response')

    # Test dispatch methods
    process._dispatch_on_init(mock_host)
    process._dispatch_on_connected(mock_host)
    process._dispatch_on_request(mock_host, request)
    process._dispatch_on_response(
        mock_host, request, response, request, response, "completion_key"
    )
    process._dispatch_on_tear_down(mock_host)

def test_reply(process):
    response = SimpleMessage(integer=1, string='test')
    process.reply(response)
    process.iris_handle.dispatchReply.assert_called_once()
