"""Unit tests for _Utils — no live IRIS instance required."""
from dataclasses import dataclass
import os
import pytest
from unittest.mock import patch, MagicMock

from iop.migration.utils import _Utils
from iop.messages.base import _Message as Message
from iop.messages.base import _PydanticMessage as PydanticMessage
from iop import BusinessOperation, Field, PersistentMessage


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

    def test_register_file_detects_polling_business_service(self, tmp_path):
        module_file = tmp_path / "bs.py"
        module_file.write_text(
            "from iop import PollingBusinessService\n\n"
            "class MyService(PollingBusinessService):\n"
            "    pass\n"
        )

        with patch.object(_Utils, "register_component") as mock_register:
            _Utils._register_file("bs.py", str(tmp_path), 1, "Python")

        mock_register.assert_called_once_with(
            "bs", "MyService", str(tmp_path), 1, "Python.bs.MyService"
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

    def test_load_settings_uses_file_stem_as_module_name(self, tmp_path):
        demo_file = tmp_path / "demo.py"
        demo_file.write_text("VALUE = __name__\n")

        module, path = _Utils._load_settings(str(demo_file))
        try:
            assert module.__name__ == "demo"
            assert module.VALUE == "demo"
        finally:
            _Utils._cleanup_sys_path(path)


class TestProductionOperations:
    def test_set_productions_settings(self, tmp_path):
        class TestComponent:
            pass

        production_list = [{
            "TestProduction": {
                "Item": [{"@Name": "TestItem", "@ClassName": TestComponent}]
            }
        }]

        with patch('iop.migration.utils._Utils.register_component') as mock_register:
            with patch('iop.migration.utils._Utils.register_production') as mock_prod:
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

        with patch('iop.migration.utils._Utils.register_schema') as mock_register:
            _Utils.register_message_schema(TestMessage)
            mock_register.assert_called_once()

        with patch('iop.migration.utils._Utils.register_schema') as mock_register:
            _Utils.register_message_schema(TestMessageSchema)
            mock_register.assert_called_once()

        with pytest.raises(ValueError):
            _Utils.register_message_schema(FailMessage)

    def test_register_schema(self):
        with patch('iris.cls') as mock_cls:
            _Utils.register_schema("test.schema", "{}", "test")
            mock_cls.return_value.Import.assert_called_once()


class TestMigrationPlan:
    def test_explain_migration_with_messages(self, tmp_path):
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(
            "from dataclasses import dataclass\n"
            "from iop import BusinessOperation, Field, Message, PersistentMessage\n\n"
            "class MyOperation(BusinessOperation):\n"
            "    pass\n\n"
            "class NativeOrder(PersistentMessage):\n"
            "    OrderId: str = Field(required=True)\n\n"
            "@dataclass\n"
            "class DtlMessage(Message):\n"
            "    value: str = ''\n\n"
            "CLASSES = {\n"
            "    'Python.MyOperation': MyOperation,\n"
            "    'Demo.Msg.NativeOrder': NativeOrder,\n"
            "}\n"
            "SCHEMAS = [DtlMessage]\n"
            "PRODUCTIONS = [{'Demo.Production': {'Item': []}}]\n"
        )

        plan = _Utils.explain_migration(
            str(settings_file), mode="LOCAL", namespace="USER"
        )

        assert "Mode: LOCAL" in plan
        assert "Namespace: USER" in plan
        assert "CLASSES:" in plan
        assert "Python.MyOperation -> settings.MyOperation (component)" in plan
        assert (
            "Demo.Msg.NativeOrder -> settings.NativeOrder (PersistentMessage)"
            in plan
        )
        assert "SCHEMAS:\n  settings.DtlMessage" in plan
        assert "PRODUCTIONS:\n  Demo.Production" in plan

    def test_explain_migration_from_non_settings_filename_keeps_module_name(
        self, tmp_path
    ):
        demo_file = tmp_path / "demo.py"
        demo_file.write_text(
            "from iop import BusinessOperation, Production\n\n"
            "class MyOperation(BusinessOperation):\n"
            "    pass\n\n"
            "prod = Production('Demo.Production')\n"
            "prod.operation(MyOperation)\n"
            "PRODUCTIONS = [prod]\n"
        )

        plan = _Utils.explain_migration(str(demo_file), mode="LOCAL")

        assert "Demo.Production" in plan
        assert "demo.MyOperation" in plan
        assert "settings.MyOperation" not in plan

    def test_message_in_classes_gets_actionable_error(self):
        @dataclass
        class TestMessage(Message):
            value: str = ""

        class Settings:
            CLASSES = {"Python.TestMessage": TestMessage}

        with pytest.raises(ValueError, match="cannot be registered in CLASSES"):
            _Utils._build_migration_plan(Settings, os.getcwd())

    def test_register_settings_components_and_schemas(self, tmp_path):
        class MyOperation(BusinessOperation):
            pass

        class NativeOrder(PersistentMessage):
            OrderId: str = Field(required=True)

        @dataclass
        class DtlMessage(Message):
            value: str = ""

        class Settings:
            CLASSES = {
                "Python.MyOperation": MyOperation,
                "Demo.Msg.NativeOrder": NativeOrder,
            }
            SCHEMAS = [DtlMessage]

        with patch.object(_Utils, "register_component") as mock_component:
            with patch.object(_Utils, "register_persistent_message") as mock_native:
                with patch.object(_Utils, "register_message_schema") as mock_schema:
                    _Utils._register_settings_components(Settings, str(tmp_path))

        mock_component.assert_called_once_with(
            MyOperation.__module__,
            "MyOperation",
            str(tmp_path),
            1,
            "Python.MyOperation",
        )
        mock_native.assert_called_once_with(NativeOrder, "Demo.Msg.NativeOrder")
        mock_schema.assert_called_once_with(DtlMessage)


class TestXmlToJson:
    def test_production_key_replaced_with_name(self):
        xml = '<Production Name="MyApp.Production"><Item Name="A"/></Production>'
        result = _Utils.xml_to_json(xml)
        import json
        data = json.loads(result)
        assert "MyApp.Production" in data
        assert "Production" not in data

    def test_none_values_become_empty_string(self):
        xml = '<Production Name="P"><Item/></Production>'
        result = _Utils.xml_to_json(xml)
        import json
        data = json.loads(result)
        # should not raise and values should not be None
        assert data["P"]["Item"] is not None

    def test_fallback_key_when_no_name_attr(self):
        xml = '<Production><Item Name="A"/></Production>'
        result = _Utils.xml_to_json(xml)
        import json
        data = json.loads(result)
        # falls back to 'Production' when @Name is absent
        assert "Production" in data
