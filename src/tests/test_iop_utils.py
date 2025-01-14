import pytest
import iris
import os
import sys
from iop._utils import _Utils
from unittest.mock import patch, MagicMock

@pytest.fixture
def test_path():
    """Fixture to get the path of the current test directory"""
    return os.path.dirname(os.path.realpath(__file__))

@pytest.fixture
def register_path(test_path):
    """Fixture to get the path of the register files"""
    return os.path.join(test_path, 'registerFilesIop')

class TestFileOperations:
    def test_filename_to_module(self):
        assert _Utils.filename_to_module('bo.py') == 'bo'

    def test_raise_on_error(self):
        with pytest.raises(RuntimeError):
            sc = iris.system.Status.Error('test')
            _Utils.raise_on_error(sc)

    def test_setup_succeeds(self):
        _Utils.setup()

class TestComponentRegistration:
    @pytest.mark.parametrize("module,classname,iris_classname", [
        ('bo', 'EmailOperation', 'UnitTest.EmailOperation'),
        # Add more test cases here
    ])
    def test_register_component(self, register_path, module, classname, iris_classname):
        _Utils.register_component(
            module, 
            classname, 
            register_path, 
            overwrite=1, 
            iris_classname=iris_classname
        )

    def test_register_component_fails_on_iris_error(self, register_path):
        with patch('iris.cls', side_effect=RuntimeError):
            with pytest.raises(RuntimeError):
                _Utils.register_component(
                    'bo', 
                    'EmailOperation', 
                    register_path, 
                    1, 
                    'UnitTest.EmailOperation'
                )

class TestStreamOperations:
    @pytest.mark.parametrize("input_string,expected", [
        ('test', 'test'),
        ('', ''),
        ('test'*1000, 'test'*1000),
    ])
    def test_string_stream_conversion(self, input_string, expected):
        # Test string to stream to string roundtrip
        stream = _Utils.string_to_stream(input_string)
        result = _Utils.stream_to_string(stream)
        assert result == expected
