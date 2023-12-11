import pickle
import codecs
from datetime import datetime, date, time
from unittest.mock import MagicMock

from grongier.pex._business_host import _BusinessHost

from grongier.pex import Message

from registerFiles.message import TestSimpleMessage, TestSimpleMessageNotMessage, TestPickledMessage, FullMessage, PostMessage, MyResponse

from registerFiles.obj import PostClass

def test_dispatch_serializer():
    bh = _BusinessHost()

def test_serialize_message_decorator():
    bh = _BusinessHost()
    msg = TestSimpleMessage(integer=1, string='test')
    msg_serialized = bh._serialize_message(msg)
    # Mock iris_handler
    bh.iris_handle = MagicMock()

    bh.send_request_sync(target='test', request=msg)
    bh.iris_handle.dispatchSendRequestSync.assert_called_once()
    assert bh.iris_handle.dispatchSendRequestSync.call_args[0][0] == 'test'
    assert type(bh.iris_handle.dispatchSendRequestSync.call_args[0][1]) == type(msg_serialized)

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

def test_deseialize_message_japanese():
    bh = _BusinessHost()
    msg = TestSimpleMessage(integer=1, string='あいうえお')
    result = bh._serialize_message(msg)
    assert result.json == '{"integer": 1, "string": "あいうえお"}'
    msg = bh._deserialize_message(result)
    assert msg.integer == 1
    assert msg.string == 'あいうえお'

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
    # way around 
    msg = bh._deserialize_pickle_message(result)
    assert msg.integer == 1
    assert msg.string == 'test'

def test_fullmessage():
    postclass = PostClass(
        Selftext='test',
        Title='test',
        Url='test',
        Author='test',
        CreatedUTC=1.1,
        OriginalJSON='test',
    )
    msg = FullMessage(
        embedded=postclass,
        embedded_list=['test'],
        embedded_dict={'test':postclass},
        string='test',
        integer=1,
        float=1.0,
        boolean=True,
        list=['test'],
        dict={'test':'test'},
        list_dict=[{'test':'test'}],
        dict_list={'test':['test']},
        date=date(2020, 1, 1),
        datetime=datetime(2020, 1, 1, 1, 1, 1),
        time=time(1, 1, 1)
    )
    bh = _BusinessHost()
    tmp = bh._serialize_message(msg)
    result = bh._deserialize_message(tmp)
    assert result.embedded.Selftext == 'test'
    assert result.embedded_list[0] == 'test'
    assert result.embedded_dict['test'].Selftext == 'test'
    assert result.string == 'test'
    assert result.integer == 1
    assert result.float == 1.0
    assert result.boolean
    assert result.list[0] == 'test'
    assert result.dict['test'] == 'test'
    assert result.list_dict[0]['test'] == 'test'
    assert result.dict_list['test'][0] == 'test'
    assert result.date == date(2020, 1, 1)
    assert result.datetime == datetime(2020, 1, 1, 1, 1, 1)
    assert result.time == time(1, 1, 1)


