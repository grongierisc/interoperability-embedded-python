"""Unit tests for _Utils — no live IRIS instance required."""
from dataclasses import dataclass
import os
import pytest
from unittest.mock import patch, MagicMock

from iop._utils import _Utils
from iop._message import _Message as Message
from iop._message import _PydanticMessage as PydanticMessage


@pytest.fixture
def test_path():
    return os.path.dirname(os.path.realpath(__file__))


@pytest.fixture
def register_path(test_path):
    return os.path.join(test_path, '..', 'fixtures')


class TestFileOperations:
    def test_filename_to_module(self):
        assert _Utils.filename_to_module('bo.py') == 'bo'


class TestComponentRegistration:
    def test_register_component_fails_on_iris_error(self, register_path):
        with patch('iris.cls', side_effect=RuntimeError):
            with pytest.raises(RuntimeError):
                _Utils.register_component(
                    'bo', 'EmailOperation', register_path, 1, 'UnitTest.EmailOperation'
                )


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
        module_file = tmp_path / "test_module.py"
        module_file.write_text("TEST_VARIABLE = 'test_value'")

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
                "Item": [{"@Name": "TestItem", "@ClassName": TestComponent}]
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


class TestRemoteMigration:
    @patch('requests.put')
    @patch('iop._utils._Utils._load_settings')
    @patch('os.walk')
    def test_migrate_remote_verify_ssl_true(self, mock_walk, mock_load_settings, mock_put):
        mock_load_settings.return_value = (
            MagicMock(
                REMOTE_SETTINGS={
                    'url': 'http://test.com', 'verify_ssl': True,
                    'username': 'user', 'password': 'password',
                    'namespace': 'USER', 'remote_folder': '/remote',
                }
            ),
            '/path/to/sys',
        )
        mock_walk.return_value = []
        mock_put.return_value.status_code = 200
        mock_put.return_value.text = '{"status": "OK"}'

        _Utils.migrate_remote('settings.py')

        mock_put.assert_called_once()
        assert mock_put.call_args[1]['verify'] is True

    @patch('requests.put')
    @patch('iop._utils._Utils._load_settings')
    @patch('os.walk')
    def test_migrate_remote_verify_ssl_false(self, mock_walk, mock_load_settings, mock_put):
        mock_load_settings.return_value = (
            MagicMock(
                REMOTE_SETTINGS={
                    'url': 'http://test.com', 'verify_ssl': False,
                    'username': 'user', 'password': 'password',
                }
            ),
            '/path/to/sys',
        )
        mock_walk.return_value = []
        mock_put.return_value.status_code = 200
        mock_put.return_value.text = '{"status": "OK"}'

        _Utils.migrate_remote('settings.py')

        mock_put.assert_called_once()
        assert mock_put.call_args[1]['verify'] is False
