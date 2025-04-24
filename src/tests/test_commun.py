import iris
import os
import sys
import random
import string
import pytest
from iop._message_validator import is_iris_object_instance, is_message_class, is_pickle_message_class
from registerFilesIop.message import SimpleMessage, SimpleMessageNotMessage, PickledMessage
from iop._common import _Common

# Constants
INSTALL_DIR = os.getenv('IRISINSTALLDIR', None) or os.getenv('ISC_PACKAGE_INSTALLDIR', None)
MESSAGE_LOG_PATH = os.path.join(INSTALL_DIR, 'mgr', 'messages.log')

@pytest.fixture
def common():
    return _Common()

@pytest.fixture
def random_string(length=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

@pytest.fixture
def random_japanese(length=10):
    letters = 'あいうえお'
    return ''.join(random.choice(letters) for _ in range(length))

class TestMessageClassification:
    def test_is_message_class(self):
        assert is_message_class(SimpleMessage) == True
        assert is_message_class(SimpleMessageNotMessage) == False

    def test_is_pickle_message_class(self):
        assert is_pickle_message_class(PickledMessage) == True
        assert is_pickle_message_class(SimpleMessageNotMessage) == False

    def test_is_iris_object_instance(self):
        msg = iris.cls('Ens.Request')._New()
        assert is_iris_object_instance(msg) == True
        assert is_iris_object_instance(SimpleMessageNotMessage) == False
        
        msg_job = iris.cls('Ens.Job')._New()
        assert is_iris_object_instance(msg_job) == False

class TestLogging:

    def test_log_info_loggger(self, common, random_string):
        common.logger.info(random_string)
        rs = self._check_log_entry(random_string, 'test_log_info_loggger')
        for entry in rs:
            assert random_string in entry[9]

    def test_log_info_loggger_to_console(self, common, random_string):
        common.log_to_console = True
        common.logger.info(random_string)

        with open(MESSAGE_LOG_PATH, 'r') as file:
            last_line = file.readlines()[-1]
            assert random_string in last_line

    def test_log_info_to_console(self, common, random_string):
        common.log_to_console = True
        common.log_info(random_string)
        
        with open(MESSAGE_LOG_PATH, 'r') as file:
            last_line = file.readlines()[-1]
            assert random_string in last_line

    def test_log_info_to_console_from_method(self, common, random_string):
        common.trace(message=random_string, to_console=True)
        
        with open(MESSAGE_LOG_PATH, 'r') as file:
            last_line = file.readlines()[-1]
            assert random_string in last_line

    def _check_log_entry(self, message, method_name, level=4):
        sql = """
            SELECT * FROM Ens_Util.Log 
            WHERE SourceClass = '_Common' 
            AND SourceMethod = ? 
            AND Text = ? 
            AND Type = ?
            ORDER BY id DESC
        """
        stmt = iris.sql.prepare(sql)
        rs = stmt.execute(method_name, message, level)
        if rs is None:
            return []
        return rs

    def test_log_info(self, common, random_string):
        common.log_info(random_string)
        rs = self._check_log_entry(random_string, 'test_log_info')
        for entry in rs:
            assert random_string in entry[9]

    def test_log_warning(self, common, random_string):
        common.log_warning(random_string)
        rs = self._check_log_entry(random_string, 'test_log_info', 3)
        for entry in rs:
            assert random_string in entry[9]

    def test_log_info_japanese(self, common, random_japanese):
        common.log_info(random_japanese)
        rs = self._check_log_entry(random_japanese, 'test_log_info_japanese')
        for entry in rs:
            assert random_japanese in entry[9]

class TestBusinessService:
    def test_get_info(self):
        path = os.path.dirname(os.path.realpath(__file__))
        sys.path.append(path)
        
        from registerFilesIop.edge.bs_underscore import BS
        result = BS._get_info()
        expected = ['iop.BusinessService', '', '', '', 'EnsLib.File.InboundAdapter']
        
        assert result == expected
