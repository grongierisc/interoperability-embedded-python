import pytest
from unittest.mock import MagicMock

from iop.components.inbound_adapter import _InboundAdapter
from iop.components.outbound_adapter import _OutboundAdapter

@pytest.fixture
def inbound_adapter():
    adapter = _InboundAdapter()
    adapter.iris_handle = MagicMock()
    return adapter

@pytest.fixture
def outbound_adapter():
    adapter = _OutboundAdapter()
    adapter.iris_handle = MagicMock()
    return adapter

class TestInboundAdapter:
    def test_set_iris_handles(self, inbound_adapter):
        handle_current = MagicMock()
        handle_partner = MagicMock()
        handle_partner.GetClass = MagicMock(return_value="TestClass")
        
        inbound_adapter._set_iris_handles(handle_current, handle_partner)
        
        assert inbound_adapter.iris_handle == handle_current
        assert inbound_adapter.BusinessHost == handle_partner
        assert inbound_adapter.business_host == handle_partner
        assert inbound_adapter.business_host_python == "TestClass"

    def test_on_task_default(self, inbound_adapter):
        assert inbound_adapter.on_task() is None
        assert not hasattr(inbound_adapter, "OnTask")

class TestOutboundAdapter:
    def test_set_iris_handles(self, outbound_adapter):
        handle_current = MagicMock()
        handle_partner = MagicMock()
        handle_partner.GetClass = MagicMock(return_value="TestClass")
        
        outbound_adapter._set_iris_handles(handle_current, handle_partner)
        
        assert outbound_adapter.iris_handle == handle_current
        assert outbound_adapter.BusinessHost == handle_partner
        assert outbound_adapter.business_host == handle_partner
        assert outbound_adapter.business_host_python == "TestClass"

    def test_on_keepalive(self, outbound_adapter):
        assert outbound_adapter.on_keepalive() is None
