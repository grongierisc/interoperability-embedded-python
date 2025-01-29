from dataclasses import dataclass
import pytest
import iris
import os
import sys
from iop._utils import _Utils
from iop._message import _Message as Message
from iop._message import _PydanticMessage as PydanticMessage
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
        ('bo', 'MyOperation', 'UnitTest.MyOperation'),
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

class TestPathOperations:
    @pytest.mark.parametrize("module,path,expected", [
        ('module', '/path/to', '/path/to/module.py'),
        ('pkg.module', '/path/to', '/path/to/pkg/module.py'),
        ('.module', '/path/to', '/path/to/module.py'),
        ('..module', '/path/to/sub', '/path/to/module.py'),
    ])
    def test_guess_path(self, module, path, expected):
        result = _Utils.guess_path(module, path)
        assert os.path.normpath(result) == os.path.normpath(expected)

class TestModuleOperations:
    def test_import_module_from_path(self, tmp_path):
        # Create a temporary module file
        module_content = "TEST_VARIABLE = 'test_value'"
        module_file = tmp_path / "test_module.py"
        module_file.write_text(module_content)
        
        module = _Utils.import_module_from_path("test_module", str(module_file))
        assert module.TEST_VARIABLE == 'test_value'

    def test_import_module_invalid_path(self):
        with pytest.raises(ValueError):
            _Utils.import_module_from_path("invalid", "relative/path")

class TestProductionOperations:
    def test_set_productions_settings(self, tmp_path):
        class TestComponent:
            pass

        production_list = [{
            "TestProduction": {
                "Item": [{
                    "@Name": "TestItem",
                    "@ClassName": TestComponent
                }]
            }
        }]

        with patch('iop._utils._Utils.register_component') as mock_register:
            with patch('iop._utils._Utils.register_production') as mock_prod:
                _Utils.set_productions_settings(production_list, str(tmp_path))
                mock_register.assert_called_once()
                mock_prod.assert_called_once()


class TestSchemaOperations:
    def test_register_message_schema(self):
        @dataclass
        class TestMessage(Message):
            test: str

        class TestMessageSchema(PydanticMessage):
            test: str

        class FailMessage:
            pass

        with patch('iop._utils._Utils.register_schema') as mock_register:
            _Utils.register_message_schema(TestMessage)
            mock_register.assert_called_once()

        with patch('iop._utils._Utils.register_schema') as mock_register:
            _Utils.register_message_schema(TestMessageSchema)
            mock_register.assert_called_once()

        with pytest.raises(ValueError):
            _Utils.register_message_schema(FailMessage)

    def test_register_schema(self):
        with patch('iris.cls') as mock_cls:
            _Utils.register_schema("test.schema", "{}", "test")
            mock_cls.return_value.Import.assert_called_once()
