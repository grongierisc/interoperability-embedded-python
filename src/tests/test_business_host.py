import pickle
import asyncio
import iris
import codecs
from datetime import datetime, date, time
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from iop._business_host import _BusinessHost
from iop._dispatch import deserialize_message, deserialize_pickle_message, dispach_message, dispatch_serializer, serialize_message, serialize_pickle_message
from registerFilesIop.message import (
    SimpleMessage, SimpleMessageNotMessage, SimpleMessageNotDataclass, 
    PickledMessage, FullMessage, PostMessage, MyResponse
)
from registerFilesIop.obj import PostClass
from registerFilesIop.bs import RedditService
from registerFilesIop.bo import FileOperation

@pytest.fixture
def business_host():
    bh = _BusinessHost()
    bh.iris_handle = MagicMock()
    return bh

class TestBusinessHostAsync:
    @pytest.mark.asyncio
    @patch('iop._async_request.dispatch_deserializer')
    async def test_send_request_async_ng(self, mock_deserializer, business_host):
        business_host.iris_handle.dispatchSendRequestAsyncNG = MagicMock()
        business_host.iris_handle.dispatchIsRequestDone.return_value = 2
        mock_deserializer.return_value = MyResponse(value='test')

        result = await business_host.send_request_async_ng('test', SimpleMessage(integer=1, string='test'))
        
        assert result == MyResponse(value='test')
        mock_deserializer.assert_called_once()

    def test_send_multi_request_sync(self, business_host):
        business_host.iris_handle.dispatchSendRequestSyncMultiple = MagicMock()
        rsp = iris.cls("Ens.CallStructure")._New()
        rsp.Response = MyResponse(value='test')
        rsp.ResponseCode = 1
        business_host.iris_handle.dispatchSendRequestSyncMultiple.return_value = [rsp]
        
        result = business_host.send_multi_request_sync([('test', SimpleMessage(integer=1, string='test'))])
        
        assert result == [('test', SimpleMessage(integer=1, string='test'), MyResponse(value='test'), 1)]

class TestGeneratorRequest:
    def test_generator_request_initialization(self, business_host):
        business_host.iris_handle.dispatchSendRequestSync = MagicMock()
        business_host.iris_handle.dispatchSendRequestSync.return_value = iris.cls("IOP.Generator.Message.Ack")._New()

        from iop._generator_request import _GeneratorRequest
        generator = _GeneratorRequest(business_host, "test_target", SimpleMessage(integer=1, string='test'))

        assert generator.host == business_host
        assert generator.target == "test_target"
        assert generator.request == SimpleMessage(integer=1, string='test')

    @patch('iop._business_host._iris.get_iris')
    @patch('iop._business_host.dispach_message')
    def test_dispatch_generator_started(self, mock_dispatch, mock_iris, business_host):
        mock_generator = iter([1, 2, 3])
        mock_dispatch.return_value = mock_generator
        mock_ack = MagicMock()
        mock_iris.return_value.IOP.Generator.Message.Ack._New.return_value = mock_ack
        
        result = business_host._dispatch_generator_started("request")
        
        assert result == mock_ack
        assert hasattr(business_host, '_gen')

    @patch('iop._business_host.dispach_message')
    def test_dispatch_generator_started_not_iterable(self, mock_dispatch, business_host):
        mock_dispatch.return_value = SimpleMessage(integer=1, string='test')
        
        with pytest.raises(TypeError):
            business_host._dispatch_generator_started("request")

    def test_dispatch_generator_poll_next(self, business_host):
        # Configure the mock to return proper buffer size
        mock_msg = SimpleMessage(integer=1, string='test')
        
        business_host._gen = iter([SimpleMessage(integer=1, string='test'), SimpleMessage(integer=2, string='test2')])
        
        result = business_host._dispatch_generator_poll()

        # deserialize the message
        result = deserialize_message(result)
        
        assert result == SimpleMessage(integer=1, string='test')

    def test_dispatch_generator_poll_stop(self, business_host):
        business_host._gen = iter([])
        
        result = business_host._dispatch_generator_poll()
        
        assert result._IsA("IOP.Generator.Message.Stop")

class TestMessageSerialization:
    def test_dispatch_serializer_valid(self, business_host):
        message = SimpleMessage(integer=1, string='test')
        rsp = dispatch_serializer(message)
        
        assert rsp.classname == 'registerFilesIop.message.SimpleMessage'
        assert rsp.GetObjectJson() == '{"integer":1,"string":"test"}'

    def test_dispatch_serializer_none(self, business_host):
        assert dispatch_serializer(None) is None

    @pytest.mark.parametrize("invalid_message,expected_error", [
        (SimpleMessageNotMessage(), TypeError),
        (SimpleMessageNotDataclass(), TypeError),
        ("test", TypeError)
    ])
    def test_dispatch_serializer_invalid(self, invalid_message, expected_error):
        with pytest.raises(expected_error):
            dispatch_serializer(invalid_message)

class TestMessageDeserialization:
    def test_serialize_deserialize_simple(self):
        original = SimpleMessage(integer=1, string='test')
        serialized = serialize_message(original)
        deserialized = deserialize_message(serialized)
        
        assert deserialized.integer == original.integer
        assert deserialized.string == original.string

    def test_serialize_deserialize_japanese(self):
        original = SimpleMessage(integer=1, string='あいうえお')
        serialized = serialize_message(original)
        deserialized = deserialize_message(serialized)
        
        assert deserialized.string == 'あいうえお'

    def test_serialize_deserialize_large_string(self):
        huge_string = 'test' * 1000000
        original = SimpleMessage(integer=1, string=huge_string)
        serialized = serialize_message(original)
        deserialized = deserialize_message(serialized)
        
        assert deserialized.string == huge_string

class TestPickledMessages:
    def test_pickled_message_roundtrip(self):
        original = PickledMessage(integer=1, string='test')
        serialized = serialize_pickle_message(original)
        deserialized = deserialize_pickle_message(serialized)
        
        assert deserialized.integer == original.integer
        assert deserialized.string == original.string

class TestBusinessService:
    def test_dispatch_message(self):
        bs = FileOperation()
        bs.PutLine = MagicMock()
        bs.Limit = 1
        bs.on_init()
        
        post = PostClass(Title='test', Selftext='test', Url='test', 
                        Author='test', CreatedUTC=1.1, OriginalJSON='test')
        message = PostMessage(Post=post, Found='True', ToEmailAddress='test')
        
        dispach_message(bs,message)

    def test_reddit_service_connections(self):
        bs = RedditService()
        bs.Limit = 1
        bs.on_init()
        connections = bs.on_get_connections()
        
        assert len(connections) == 1
