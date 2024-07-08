import iris

import os
import sys

import intersystems_iris.dbapi._DBAPI as irisdbapi

from registerFilesIop.message import TestSimpleMessage, TestSimpleMessageNotMessage, TestPickledMessage

from iop._common import _Common


def test_is_message_class():
    # test if the message is an iop.Message instance
    result = _Common._is_message_class(TestSimpleMessage)
    assert result == True
    # test not a message class
    result = _Common._is_message_class(TestSimpleMessageNotMessage)
    assert result == False

def test_is_pickle_message_class():
    # test if the message is an iop.Message instance
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

def test_log_info_japanese():
    commun = _Common()
    # generate a random string of 10 characters which contains japanese characters
    import random
    letters = 'あいうえお'
    random_string = ''.join(random.choice(letters) for i in range(10))
    commun.log_info(random_string)
    sql = "SELECT * FROM Ens_Util.Log where SourceClass = '_Common' and SourceMethod = 'test_log_info_japanese' and Text = ? order by id desc"
    with irisdbapi.connect(embedded=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, (random_string,))
            rs = cursor.fetchall()
            assert len(rs) == 1

def test_get_info():
    # set python path to the registerFiles folder
    path = os.path.dirname(os.path.realpath(__file__))

    sys.path.append(path)

    from registerFilesIop.edge.bs_underscore import BS

    result = BS._get_info()

    expect = ['iop.BusinessService','','','', 'EnsLib.File.InboundAdapter']

    assert result == expect