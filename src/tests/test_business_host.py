import iris
import pickle
import codecs

from grongier.pex._business_host import _BusinessHost

from registerFiles.message import TestSimpleMessage, TestSimpleMessageNotMessage, TestPickledMessage

def test_dispatch_serializer():
    bh = _BusinessHost()

def test_serialize_message():
    bh = _BusinessHost()
    msg = TestSimpleMessage(integer=1, string='test')
    result = bh._serialize_message(msg)
    result.jstr.Rewind()
    stream = result.jstr.Read()
    assert result.classname == 'registerFiles.message.TestSimpleMessage'
    assert result.json == '{"integer": 1, "string": "test"}'
    assert stream == '{"integer": 1, "string": "test"}'

def test_deseialize_message():
    bh = _BusinessHost()
    msg = TestSimpleMessage(integer=1, string='test')
    result = bh._serialize_message(msg)
    assert result.json == '{"integer": 1, "string": "test"}'
    msg = bh._deserialize_message(result)
    assert msg.integer == 1
    assert msg.string == 'test'

def test_serialize_pickled_message():
    bh = _BusinessHost()
    msg = TestPickledMessage(integer=1, string='test')
    result = bh._serialize_pickle_message(msg)
    result.jstr.Rewind()
    stream = result.jstr.Read()
    # convert TestPickledMessage to a pickle and encode it in base64
    pickled = pickle.dumps(msg)
    pickled = codecs.encode(pickled, "base64").decode()
    assert result.classname == 'registerFiles.message.TestPickledMessage'
    assert stream == pickled

def test_deseialize_pickled_message():
    bh = _BusinessHost()
    msg = TestPickledMessage(integer=1, string='test')
    result = bh._serialize_pickle_message(msg)
    # convert TestPickledMessage to a pickle and encode it in base64
    pickled = pickle.dumps(msg)
    pickled = codecs.encode(pickled, "base64").decode()
    msg = bh._deserialize_pickle_message(result)
    assert msg.integer == 1
    assert msg.string == 'test'