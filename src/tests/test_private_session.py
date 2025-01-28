import pytest
from unittest.mock import MagicMock, patch

from iop._private_session_duplex import _PrivateSessionDuplex
from iop._private_session_process import _PrivateSessionProcess
from registerFilesIop.message import SimpleMessage, MyResponse

@pytest.fixture
def duplex():
    duplex = _PrivateSessionDuplex()
    duplex.iris_handle = MagicMock()
    return duplex

@pytest.fixture
def process():
    process = _PrivateSessionProcess()
    process.iris_handle = MagicMock()
    return process

class TestPrivateSessionDuplex:
    def test_set_iris_handles_with_iris_adapter(self, duplex):
        handle_current = MagicMock()
        handle_partner = MagicMock()
        handle_partner._IsA = MagicMock(return_value=True)
        handle_partner.GetModule = MagicMock(return_value="test_module")
        handle_partner.GetClassname = MagicMock(return_value="TestAdapter")
        
        with patch('importlib.import_module') as mock_import:
            mock_module = MagicMock()
            mock_adapter = MagicMock()
            mock_module.TestAdapter = mock_adapter
            mock_import.return_value = mock_module
            
            duplex._set_iris_handles(handle_current, handle_partner)
            
            assert duplex.iris_handle == handle_current

    def test_send_document_to_process(self, duplex):
        document = SimpleMessage(integer=1, string='test')
        duplex.iris_handle.dispatchSendDocumentToProcess = MagicMock(return_value=MyResponse(value='test'))
        
        result = duplex.send_document_to_process(document)
        
        duplex.iris_handle.dispatchSendDocumentToProcess.assert_called_once()
        assert isinstance(result, MyResponse)
        assert result.value == 'test'

class TestPrivateSessionProcess:
    def test_dispatch_on_private_session_stopped(self, process):
        host_object = MagicMock()
        test_request = SimpleMessage(integer=1, string='test')
        
        with patch.object(process, 'on_private_session_stopped', return_value=MyResponse(value='test')) as mock_handler:
            result = process._dispatch_on_private_session_stopped(host_object, 'test_source', 'self_generated', test_request)
            
            mock_handler.assert_called_once()
            assert result.json == '{"value":"test"}'

    def test_dispatch_on_private_session_started(self, process):
        host_object = MagicMock()
        test_request = SimpleMessage(integer=1, string='test')
        
        with patch.object(process, 'on_private_session_started', return_value=MyResponse(value='test')) as mock_handler:
            result = process._dispatch_on_private_session_started(host_object, 'test_source', test_request)
            
            mock_handler.assert_called_once()
            assert result.json == '{"value":"test"}'

    def test_dispatch_on_document(self, process):
        host_object = MagicMock()
        test_request = SimpleMessage(integer=1, string='test')
        
        with patch.object(process, 'on_document', return_value=MyResponse(value='test')) as mock_handler:
            result = process._dispatch_on_document(host_object, 'test_source', test_request)
            
            mock_handler.assert_called_once()
            assert result.json == '{"value":"test"}'
