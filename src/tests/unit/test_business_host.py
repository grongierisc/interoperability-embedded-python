"""Unit tests for _BusinessHost — no live IRIS instance required."""
from unittest.mock import MagicMock, patch

import pytest
from fixtures.bs import RedditService
from fixtures.message import (
    MyResponse,
    SimpleMessage,
    SimpleMessageNotDataclass,
    SimpleMessageNotMessage,
)

from iop.components.business_host import _BusinessHost
from iop.messages.dispatch import dispatch_serializer


@pytest.fixture
def business_host():
    bh = _BusinessHost()
    bh.iris_handle = MagicMock()
    return bh


class TestBusinessHostAsync:
    @pytest.mark.asyncio
    @patch('iop.components.async_request.dispatch_deserializer')
    async def test_send_request_async_ng(self, mock_deserializer, business_host):
        business_host.iris_handle.dispatchSendRequestAsyncNG = MagicMock()
        business_host.iris_handle.dispatchIsRequestDone.return_value = 2
        mock_deserializer.return_value = MyResponse(value='test')

        result = await business_host.send_request_async_ng('test', SimpleMessage(integer=1, string='test'))

        assert result == MyResponse(value='test')
        mock_deserializer.assert_called_once()


class TestGeneratorRequest:
    @patch('iop.components.business_host._iris.get_iris')
    @patch('iop.components.business_host.dispatch_message')
    def test_dispatch_generator_started(self, mock_dispatch, mock_iris, business_host):
        mock_generator = iter([1, 2, 3])
        mock_dispatch.return_value = mock_generator
        mock_ack = MagicMock()
        mock_iris.return_value.IOP.Generator.Message.Ack._New.return_value = mock_ack

        result = business_host._dispatch_generator_started("request")

        assert result == mock_ack
        assert hasattr(business_host, '_gen')

    @patch('iop.components.business_host.dispatch_message')
    def test_dispatch_generator_started_not_iterable(self, mock_dispatch, business_host):
        mock_dispatch.return_value = SimpleMessage(integer=1, string='test')

        with pytest.raises(TypeError):
            business_host._dispatch_generator_started("request")


class TestMessageSerialization:
    def test_dispatch_serializer_none(self, business_host):
        assert dispatch_serializer(None) is None

    @pytest.mark.parametrize("invalid_message,expected_error", [
        (SimpleMessageNotMessage(), TypeError),
        (SimpleMessageNotDataclass(), TypeError),
        ("test", TypeError),
    ])
    def test_dispatch_serializer_invalid(self, invalid_message, expected_error):
        with pytest.raises(expected_error):
            dispatch_serializer(invalid_message)


class TestBusinessService:
    def test_reddit_service_connections(self):
        bs = RedditService()
        bs.Limit = 1
        bs.on_init()
        connections = bs.on_get_connections()

        assert len(connections) == 1

    def test_connection_discovery_does_not_call_on_init(self):
        class Service(_BusinessHost):
            target = "Python.Target"

            def on_init(self):
                raise AssertionError("on_init should not run during inspection")

            def on_message(self, request):
                return self.send_request_sync(self.target, request)

        assert Service().on_get_connections() == ["Python.Target"]

    def test_connection_discovery_includes_async_ng_and_generator_requests(self):
        class Process(_BusinessHost):
            target = "Python.Target"
            generator_target = "Python.GeneratorTarget"

            async def on_message(self, request):
                await self.send_request_async_ng(self.target, request)
                self.send_generator_request(self.generator_target, request)

        assert set(Process().on_get_connections()) == {
            "Python.Target",
            "Python.GeneratorTarget",
        }
