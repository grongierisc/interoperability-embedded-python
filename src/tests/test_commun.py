import iris

import intersystems_iris.dbapi._DBAPI as irisdbapi

from dataclasses import dataclass

from grongier.pex._common import _Common
from grongier.pex import Message, PickleMessage

@dataclass
class TestSimpleMessage(Message):
    integer : int 
    string : str

class TestSimpleMessageNotDataclass(Message):
    integer : int 
    string : str

class TestSimpleMessageNotMessage:
    integer : int 
    string : str

@dataclass
class TestPickledMessage(PickleMessage):
    integer : int 
    string : str

def test_is_message_class():
    # test if the message is an grongier.pex.Message instance
    result = _Common._is_message_class(TestSimpleMessage)
    assert result == True
    # test not a message class
    result = _Common._is_message_class(TestSimpleMessageNotMessage)
    assert result == False

def test_is_pickle_message_class():
    # test if the message is an grongier.pex.Message instance
    result = _Common._is_pickel_message_class(TestPickledMessage)
    assert result == True
    # test not a message class
    result = _Common._is_pickel_message_class(TestSimpleMessageNotMessage)
    assert result == False

def test_is_iris_object_instance():
    msg = iris.cls('Ens.Request')._New()
    result = _Common._is_iris_object_instance(msg)
    assert result == True
    # test not an iris object instance
    result = _Common._is_iris_object_instance(TestSimpleMessageNotMessage)
    assert result == False
    # test iris not persistent object
    msg = iris.cls('Ens.Job')._New()
    result = _Common._is_iris_object_instance(msg)
    assert result == False

def test_log_info():
    commun = _Common()
    # generate a random string of 10 characters
    import random, string
    letters = string.ascii_lowercase
    random_string = ''.join(random.choice(letters) for i in range(10))
    commun.log_info(random_string)
    sql = "SELECT * FROM Ens_Util.Log where SourceClass = '_Common' and SourceMethod = 'test_log_info' and Text = ? order by id desc"
    with irisdbapi.connect(embedded=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, (random_string,))
            rs = cursor.fetchall()
            assert len(rs) == 1
