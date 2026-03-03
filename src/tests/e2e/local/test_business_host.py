"""E2E (local IRIS) tests for _BusinessHost."""
import iris
import pytest
from unittest.mock import MagicMock

from iop._business_host import _BusinessHost
from iop._dispatch import (
    deserialize_message, deserialize_pickle_message,
    dispach_message, dispatch_serializer,
    serialize_message, serialize_pickle_message,
)
from fixtures.message import (
    SimpleMessage, PickledMessage, FullMessage, PostMessage, MyResponse
)
from fixtures.obj import PostClass
from fixtures.bo import FileOperation


@pytest.fixture
def business_host():
    bh = _BusinessHost()
    bh.iris_handle = MagicMock()
    return bh


class TestBusinessHostAsync:
    def test_send_multi_request_sync(self, business_host):
        business_host.iris_handle.dispatchSendRequestSyncMultiple = MagicMock()
        rsp = iris.cls("Ens.CallStructure")._New()
        rsp.Response = MyResponse(value='test')
        rsp.ResponseCode = 1
        business_host.iris_handle.dispatchSendRequestSyncMultiple.return_value = [rsp]

        result = business_host.send_multi_request_sync(
            [('test', SimpleMessage(integer=1, string='test'))]
        )

        assert result == [('test', SimpleMessage(integer=1, string='test'), MyResponse(value='test'), 1)]


class TestGeneratorRequest:
    def test_generator_request_initialization(self, business_host):
        business_host.iris_handle.dispatchSendRequestSync = MagicMock()
        business_host.iris_handle.dispatchSendRequestSync.return_value = (
            iris.cls("IOP.Generator.Message.Ack")._New()
        )

        from iop._generator_request import _GeneratorRequest
        generator = _GeneratorRequest(business_host, "test_target", SimpleMessage(integer=1, string='test'))

        assert generator.host == business_host
        assert generator.target == "test_target"
        assert generator.request == SimpleMessage(integer=1, string='test')

    def test_dispatch_generator_poll_next(self, business_host):
        business_host._gen = iter([
            SimpleMessage(integer=1, string='test'),
            SimpleMessage(integer=2, string='test2'),
        ])

        result = business_host._dispatch_generator_poll()
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

        assert rsp.classname == 'fixtures.message.SimpleMessage'
        assert rsp.GetObjectJson() == '{"integer":1,"string":"test"}'


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

        post = PostClass(
            Title='test', Selftext='test', Url='test',
            Author='test', CreatedUTC=1.1, OriginalJSON='test',
        )
        message = PostMessage(Post=post, Found='True', ToEmailAddress='test')

        dispach_message(bs, message)
