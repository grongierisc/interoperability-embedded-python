import pickle
import codecs
from datetime import datetime, date, time
from unittest.mock import MagicMock

from iop._business_host import _BusinessHost

from iop import Message

from registerFilesIop.message import TestSimpleMessage, TestSimpleMessageNotMessage, TestSimpleMessageNotDataclass, TestPickledMessage, FullMessage, PostMessage, MyResponse

from registerFilesIop.obj import PostClass

from registerFilesIop.bs import RedditService

def test_dispatch_serializer():
    bh = _BusinessHost()
    message = TestSimpleMessage(integer=1, string='test')

    rsp = bh._dispatch_serializer(message)

    assert rsp.classname == 'registerFilesIop.message.TestSimpleMessage'
    assert rsp.GetObjectJson() == '{"integer": 1, "string": "test"}'

def test_dispatch_serializer_none():
    bh = _BusinessHost()
    message = None

    rsp = bh._dispatch_serializer(message)

    assert rsp is None

def test_dispatch_serializer_not_message():
    bh = _BusinessHost()
    message = TestSimpleMessageNotMessage()

    try:
        rsp = bh._dispatch_serializer(message)
    except Exception as e:
        assert type(e) == TypeError

def test_dispatch_serializer_not_dataclass():
    bh = _BusinessHost()
    message = TestSimpleMessageNotDataclass()

    try:
        rsp = bh._dispatch_serializer(message)
    except Exception as e:
        assert type(e) == TypeError

def test_serialize_message_not_dataclass():
    bh = _BusinessHost()
    msg = TestSimpleMessageNotDataclass()
    msg.integer = 1
    msg.string = 'test'

    # Mock iris_handler
    bh.iris_handle = MagicMock()

    # expect an error
    try:
        bh.send_request_sync(target='test', request=msg)
    except Exception as e:
        assert type(e) == TypeError

def test_serialize_message_not_message():
    bh = _BusinessHost()
    msg = TestSimpleMessageNotMessage()
    msg.integer = 1
    msg.string = 'test'

    # Mock iris_handler
    bh.iris_handle = MagicMock()

    # expect an error
    try:
        bh.send_request_sync(target='test', request=msg)
    except Exception as e:
        assert type(e) == TypeError

def test_serialize_message_decorator():
    bh = _BusinessHost()
    msg = TestSimpleMessage(integer=1, string='test')
    msg_serialized = bh._serialize_message(msg)
    # Mock iris_handler
    bh.iris_handle = MagicMock()

    bh.send_request_sync(target='test', request=msg)

    assert bh.iris_handle.dispatchSendRequestSync.call_args[0][0] == 'test'
    assert type(bh.iris_handle.dispatchSendRequestSync.call_args[0][1]) == type(msg_serialized)

def test_serialize_message_decorator_by_position():
    bh = _BusinessHost()
    msg = TestSimpleMessage(integer=1, string='test')
    msg_serialized = bh._serialize_message(msg)
    # Mock iris_handler
    bh.iris_handle = MagicMock()

    bh.send_request_sync('test', msg)

    assert bh.iris_handle.dispatchSendRequestSync.call_args.args[0] == 'test'
    assert type(bh.iris_handle.dispatchSendRequestSync.call_args.args[1]) == type(msg_serialized)

def test_serialize_message():
    bh = _BusinessHost()
    msg = TestSimpleMessage(integer=1, string='test')
    result = bh._serialize_message(msg)
    result.jstr.Rewind()
    stream = result.jstr.Read()
    assert result.classname == 'registerFilesIop.message.TestSimpleMessage'
    assert result.GetObjectJson() == '{"integer": 1, "string": "test"}'
    assert stream == '{"integer": 1, "string": "test"}'

def test_deseialize_message():
    bh = _BusinessHost()
    msg = TestSimpleMessage(integer=1, string='test')
    result = bh._serialize_message(msg)
    assert result.GetObjectJson() == '{"integer": 1, "string": "test"}'
    msg = bh._deserialize_message(result)
    assert msg.integer == 1
    assert msg.string == 'test'

def test_deseialize_message_japanese():
    bh = _BusinessHost()
    msg = TestSimpleMessage(integer=1, string='あいうえお')
    result = bh._serialize_message(msg)
    assert result.GetObjectJson() == '{"integer": 1, "string": "あいうえお"}'
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
    assert result.classname == 'registerFilesIop.message.TestPickledMessage'
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

def test_dispatch_on_get_connections():
    bs = RedditService()
    bs.Limit = 1
    bs.on_init()
    _list = bs.on_get_connections()
    _list_len = _list.__len__()
    for i in range(0, _list_len):
        print(_list.__getitem__(i))
    assert len(_list) == 1