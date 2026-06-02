from unittest.mock import MagicMock, patch

import pytest
from fixtures.message import SimpleMessage

from iop import PollingBusinessService
from iop.components.business_service import _BusinessService
from iop.messages.dispatch import dispatch_deserializer


@pytest.fixture
def service():
    svc = _BusinessService()
    svc.iris_handle = MagicMock()
    return svc

def test_process_input(service):
    message = SimpleMessage(integer=1, string='test')
    with pytest.warns(RuntimeWarning, match="did not override on_message"):
        assert service.on_process_input(message) is None
    assert not hasattr(service, "OnProcessInput")

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
    with pytest.warns(RuntimeWarning, match="did not override on_message"):
        service._dispatch_on_process_input(message)
    
    # Verify the message was processed
    service.iris_handle.dispatchOnProcessInput.assert_not_called()

def test_custom_service():
    class CustomService(_BusinessService):
        def on_message(self, message):
            return SimpleMessage(integer=message.integer * 2, string=f"processed_{message.string}")
    
    service = CustomService()
    service.iris_handle = MagicMock()
    
    input_msg = SimpleMessage(integer=5, string='test')
    result = service.on_process_input(input_msg)
    
    assert isinstance(result, SimpleMessage)
    assert result.integer == 10
    assert result.string == "processed_test"


def test_custom_service_can_override_process_input():
    class CustomService(_BusinessService):
        def on_process_input(self, message):
            return SimpleMessage(
                integer=message.integer * 3,
                string=f"processed_{message.string}",
            )

    service = CustomService()
    service.iris_handle = MagicMock()

    input_msg = SimpleMessage(integer=5, string='test')
    result = service.on_process_input(input_msg)

    assert isinstance(result, SimpleMessage)
    assert result.integer == 15
    assert result.string == "processed_test"


def test_dispatch_on_process_input_supports_zero_arg_override():
    class CustomService(_BusinessService):
        def on_process_input(self):
            return SimpleMessage(integer=7, string="poll")

    service = CustomService()
    service.iris_handle = MagicMock()

    result = dispatch_deserializer(
        service._dispatch_on_process_input(SimpleMessage(integer=1, string='test'))
    )

    assert isinstance(result, SimpleMessage)
    assert result.integer == 7
    assert result.string == "poll"

def test_wait_for_next_call_interval(service):
    assert service._wait_for_next_call_interval is False


def test_polling_business_service_info():
    class PollingService(PollingBusinessService):
        pass

    info = PollingService._get_info()
    properties = PollingService._get_properties()

    assert info[0] == "iop.BusinessService"
    assert info[4] == "Ens.InboundAdapter"
    assert all(prop[0] != "CallInterval" for prop in properties)


def test_polling_business_service_dispatches_to_on_poll():
    class PollingService(PollingBusinessService):
        def on_poll(self):
            return SimpleMessage(integer=42, string="poll")

    service = PollingService()
    service.iris_handle = MagicMock()

    result = dispatch_deserializer(
        service._dispatch_on_process_input(SimpleMessage(integer=1, string='test'))
    )

    assert isinstance(result, SimpleMessage)
    assert result.integer == 42
    assert result.string == "poll"


def test_polling_business_service_default_warns():
    class PollingService(PollingBusinessService):
        pass

    service = PollingService()
    service.iris_handle = MagicMock()

    with pytest.warns(RuntimeWarning, match="did not override on_poll"):
        assert service._dispatch_on_process_input(None) is None
