"""Unit tests for _Utils — no live IRIS instance required."""

import json
import os
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest

from iop import (
    BusinessOperation,
    Field,
    PersistentMessage,
    Production,
    bind_component,
    list_bindings,
    register_component,
    unbind_component,
    unregister_component,
)
from iop.messages.base import _Message as Message
from iop.messages.base import _PydanticMessage as PydanticMessage
from iop.migration import utils as migration_utils


@pytest.fixture
def test_path():
    return os.path.dirname(os.path.realpath(__file__))


@pytest.fixture
def register_path(test_path):
    return os.path.join(test_path, "..", "fixtures")


class TestFileOperations:
    def test_filename_to_module(self):
        assert migration_utils.filename_to_module("bo.py") == "bo"


class TestComponentRegistration:
    def test_public_binding_api_is_exported(self):
        assert register_component is migration_utils.register_component
        assert bind_component is migration_utils.bind_component
        assert unregister_component is migration_utils.unregister_component
        assert unbind_component is migration_utils.unbind_component
        assert list_bindings is migration_utils.list_bindings

    def test_register_component_fails_on_iris_error(self, register_path):
        with patch("iris.cls", side_effect=RuntimeError):
            with pytest.raises(RuntimeError):
                migration_utils.register_component(
                    "bo", "EmailOperation", register_path, 1, "UnitTest.EmailOperation"
                )

    def test_unregister_component_deletes_proxy_class(self):
        iris = MagicMock()
        iris.cls.return_value.DeleteComponentProxy.return_value = "ok"
        iris.system.Status.IsError.return_value = False

        with patch.object(migration_utils._iris, "get_iris", return_value=iris):
            migration_utils.unregister_component("Python.WrongOperation")

        iris.cls.assert_called_once_with("IOP.Utils")
        iris.cls.return_value.DeleteComponentProxy.assert_called_once_with(
            "Python.WrongOperation"
        )

    def test_unregister_component_requires_class_name(self):
        with pytest.raises(ValueError, match="IRIS class name is required"):
            migration_utils.unregister_component("")

    def test_bind_component_alias_registers_component(self, register_path):
        with patch.object(migration_utils, "register_component") as mock_register:
            migration_utils.bind_component(
                "bo",
                "EmailOperation",
                register_path,
                1,
                "UnitTest.EmailOperation",
            )

        mock_register.assert_called_once_with(
            "bo",
            "EmailOperation",
            register_path,
            1,
            "UnitTest.EmailOperation",
        )

    def test_unbind_component_alias_unregisters_component(self):
        with patch.object(migration_utils, "unregister_component") as mock_unregister:
            migration_utils.unbind_component("Python.WrongOperation")

        mock_unregister.assert_called_once_with("Python.WrongOperation")

    def test_list_component_bindings_loads_json(self):
        payload = [
            {
                "class": "Python.WrongOperation",
                "module": "bo",
                "classname": "WrongOperation",
                "used": False,
                "used_by": [],
            }
        ]
        iris = MagicMock()
        iris.cls.return_value.ListComponentProxies.return_value = json.dumps(payload)

        with patch.object(migration_utils._iris, "get_iris", return_value=iris):
            result = migration_utils.list_component_bindings(unused_only=True)

        iris.cls.assert_called_once_with("IOP.Utils")
        iris.cls.return_value.ListComponentProxies.assert_called_once_with(1)
        assert result == payload

    def test_register_file_detects_polling_business_service(self, tmp_path):
        module_file = tmp_path / "bs.py"
        module_file.write_text(
            "from iop import PollingBusinessService\n\n"
            "class MyService(PollingBusinessService):\n"
            "    pass\n"
        )

        with patch.object(migration_utils, "register_component") as mock_register:
            migration_utils._register_file("bs.py", str(tmp_path), 1, "Python")

        mock_register.assert_called_once_with(
            "bs", "MyService", str(tmp_path), 1, "Python.bs.MyService"
        )


class TestPathOperations:
    @pytest.mark.parametrize(
        "module,path,expected",
        [
            ("module", "/path/to", "/path/to/module.py"),
            ("pkg.module", "/path/to", "/path/to/pkg/module.py"),
            (".module", "/path/to", "/path/to/module.py"),
            ("..module", "/path/to/sub", "/path/to/module.py"),
        ],
    )
    def test_guess_path(self, module, path, expected):
        result = migration_utils.guess_path(module, path)
        assert os.path.normpath(result) == os.path.normpath(expected)


class TestModuleOperations:
    def test_import_module_from_path(self, tmp_path):
        module_file = tmp_path / "test_module.py"
        module_file.write_text("TEST_VARIABLE = 'test_value'")

        module = migration_utils.import_module_from_path(
            "test_module", str(module_file)
        )
        assert module.TEST_VARIABLE == "test_value"

    def test_import_module_invalid_path(self):
        with pytest.raises(ValueError):
            migration_utils.import_module_from_path("invalid", "relative/path")

    def test_try_import_class_reports_import_time_errors(self, tmp_path):
        module_file = tmp_path / "broken.py"
        module_file.write_text("import missing_dependency\n\nclass Broken:\n    pass\n")

        with pytest.raises(ImportError, match="Failed to import"):
            migration_utils._try_import_class("broken", "Broken", str(tmp_path))

    def test_try_import_class_reports_missing_class(self, tmp_path):
        module_file = tmp_path / "component.py"
        module_file.write_text("class Other:\n    pass\n")

        with pytest.raises(ImportError, match="does not define class"):
            migration_utils._try_import_class("component", "Missing", str(tmp_path))

    def test_try_import_class_allows_missing_target_module(self, tmp_path):
        assert (
            migration_utils._try_import_class("missing", "Component", str(tmp_path))
            is None
        )

    def test_load_settings_uses_file_stem_as_module_name(self, tmp_path):
        demo_file = tmp_path / "demo.py"
        demo_file.write_text("VALUE = __name__\n")

        module, path = migration_utils._load_settings(str(demo_file))
        try:
            assert module.__name__ == "demo"
            assert module.VALUE == "demo"
        finally:
            migration_utils._cleanup_sys_path(path)


class TestProductionOperations:
    def test_set_productions_settings(self, tmp_path):
        class TestComponent:
            pass

        production_list = [
            {
                "TestProduction": {
                    "Item": [{"@Name": "TestItem", "@ClassName": TestComponent}]
                }
            }
        ]

        with patch("iop.migration.utils.register_component") as mock_register:
            with patch(
                "iop.migration.utils.register_production_definition"
            ) as mock_prod:
                migration_utils.set_productions_settings(production_list, str(tmp_path))
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

        with patch("iop.migration.utils.register_schema") as mock_register:
            migration_utils.register_message_schema(TestMessage)
            mock_register.assert_called_once()

        with patch("iop.migration.utils.register_schema") as mock_register:
            migration_utils.register_message_schema(TestMessageSchema)
            mock_register.assert_called_once()

        with pytest.raises(ValueError):
            migration_utils.register_message_schema(FailMessage)

    def test_register_schema(self):
        with patch("iris.cls") as mock_cls:
            migration_utils.register_schema("test.schema", "{}", "test")
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

        plan = migration_utils.explain_migration(
            str(settings_file), mode="LOCAL", namespace="USER"
        )

        assert "Mode: LOCAL" in plan
        assert "Namespace: USER" in plan
        assert "CLASSES:" in plan
        assert "Python.MyOperation -> settings.MyOperation (component)" in plan
        assert (
            "Demo.Msg.NativeOrder -> settings.NativeOrder (PersistentMessage)" in plan
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

        plan = migration_utils.explain_migration(str(demo_file), mode="LOCAL")

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
            migration_utils._build_migration_plan(Settings, os.getcwd())

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

        with patch.object(migration_utils, "register_component") as mock_component:
            with patch.object(
                migration_utils, "register_persistent_message"
            ) as mock_native:
                with patch.object(
                    migration_utils, "register_message_schema"
                ) as mock_schema:
                    migration_utils._register_settings_components(
                        Settings, str(tmp_path)
                    )

        mock_component.assert_called_once_with(
            MyOperation.__module__,
            "MyOperation",
            str(tmp_path),
            1,
            "Python.MyOperation",
        )
        mock_native.assert_called_once_with(NativeOrder, "Demo.Msg.NativeOrder")
        mock_schema.assert_called_once_with(DtlMessage)

    def test_register_settings_components_registers_production_messages_first(
        self, tmp_path
    ):
        class MyOperation(BusinessOperation):
            pass

        class NativeOrder(PersistentMessage):
            OrderId: str = Field(required=True)

        prod = Production("Demo.Production").message(
            "Demo.Msg.NativeOrder", NativeOrder
        )
        prod.operation(MyOperation)

        class Settings:
            CLASSES = {}
            PRODUCTIONS = [prod]

        calls = []

        def record_message(*args, **kwargs):
            calls.append("message")

        def record_component(*args, **kwargs):
            calls.append("component")

        def record_production(*args, **kwargs):
            calls.append("production")

        with patch.object(
            migration_utils, "register_persistent_message", side_effect=record_message
        ) as mock_native:
            with patch.object(
                migration_utils, "register_component", side_effect=record_component
            ):
                with patch.object(
                    migration_utils,
                    "register_production_definition",
                    side_effect=record_production,
                ):
                    migration_utils._register_settings_components(
                        Settings, str(tmp_path)
                    )

        mock_native.assert_called_once_with(NativeOrder, "Demo.Msg.NativeOrder")
        assert calls == ["message", "component", "production"]

    def test_register_settings_components_deduplicates_classes_and_production_messages(
        self, tmp_path
    ):
        class NativeOrder(PersistentMessage):
            OrderId: str = Field(required=True)

        prod = Production("Demo.Production").message(
            "Demo.Msg.NativeOrder",
            NativeOrder,
        )

        class Settings:
            CLASSES = {"Demo.Msg.NativeOrder": NativeOrder}
            PRODUCTIONS = [prod]

        with patch.object(
            migration_utils, "register_persistent_message"
        ) as mock_native:
            with patch.object(migration_utils, "register_production_definition"):
                migration_utils._register_settings_components(Settings, str(tmp_path))

        mock_native.assert_called_once_with(NativeOrder, "Demo.Msg.NativeOrder")

    def test_direct_class_and_production_helpers_share_persistent_message_registry(
        self, tmp_path
    ):
        class NativeOrder(PersistentMessage):
            OrderId: str = Field(required=True)

        prod = Production("Demo.Production").message(
            "Demo.Msg.NativeOrder",
            NativeOrder,
        )

        migration_utils._persistent_message_registry.clear()
        try:
            with patch.object(
                migration_utils, "register_persistent_message"
            ) as mock_native:
                migration_utils.set_classes_settings(
                    {"Demo.Msg.NativeOrder": NativeOrder},
                    root_path=str(tmp_path),
                )
                with patch.object(migration_utils, "register_production_definition"):
                    migration_utils.set_productions_settings(
                        [prod], root_path=str(tmp_path)
                    )
        finally:
            migration_utils._persistent_message_registry.clear()

        mock_native.assert_called_once_with(NativeOrder, "Demo.Msg.NativeOrder")

    def test_direct_class_and_production_helpers_reject_persistent_message_conflict(
        self, tmp_path
    ):
        class NativeOrder(PersistentMessage):
            OrderId: str = Field(required=True)

        prod = Production("Demo.Production").message(
            "Demo.Msg.OtherNativeOrder",
            NativeOrder,
        )

        migration_utils._persistent_message_registry.clear()
        try:
            with patch.object(migration_utils, "register_persistent_message"):
                migration_utils.set_classes_settings(
                    {"Demo.Msg.NativeOrder": NativeOrder},
                    root_path=str(tmp_path),
                )
                with pytest.raises(ValueError, match="already registered"):
                    with patch.object(
                        migration_utils, "register_production_definition"
                    ):
                        migration_utils.set_productions_settings(
                            [prod],
                            root_path=str(tmp_path),
                        )
        finally:
            migration_utils._persistent_message_registry.clear()

    def test_register_settings_components_rejects_persistent_message_conflicts(
        self, tmp_path
    ):
        class NativeOrder(PersistentMessage):
            OrderId: str = Field(required=True)

        prod = Production("Demo.Production").message(
            "Demo.Msg.OtherNativeOrder",
            NativeOrder,
        )

        class Settings:
            CLASSES = {"Demo.Msg.NativeOrder": NativeOrder}
            PRODUCTIONS = [prod]

        with patch.object(migration_utils, "register_persistent_message"):
            with pytest.raises(ValueError, match="already registered"):
                migration_utils._register_settings_components(Settings, str(tmp_path))

    def test_register_production_definition_uses_json_object_helper(self):
        payload = {"Production": {"@Name": "Demo.Production", "Item": []}}

        with patch("iop.migration.utils._iris.get_iris") as mock_get_iris:
            mock_iris = mock_get_iris.return_value
            mock_iris.system.Status.IsError.return_value = False

            migration_utils.register_production_definition("Demo.Production", payload)

        helper = mock_iris.cls.return_value
        helper.CreateProductionFromJSON.assert_called_once()
        assert helper.CreateProductionFromJSON.call_args.args[0] == "Demo.Production"
        assert json.loads(helper.CreateProductionFromJSON.call_args.args[1]) == payload


class TestXmlToJson:
    def test_production_key_replaced_with_name(self):
        xml = '<Production Name="MyApp.Production"><Item Name="A"/></Production>'
        result = migration_utils.xml_to_json(xml)
        import json

        data = json.loads(result)
        assert "MyApp.Production" in data
        assert "Production" not in data

    def test_none_values_become_empty_string(self):
        xml = '<Production Name="P"><Item/></Production>'
        result = migration_utils.xml_to_json(xml)
        import json

        data = json.loads(result)
        # should not raise and values should not be None
        assert data["P"]["Item"] is not None

    def test_fallback_key_when_no_name_attr(self):
        xml = '<Production><Item Name="A"/></Production>'
        result = migration_utils.xml_to_json(xml)
        import json

        data = json.loads(result)
        # falls back to 'Production' when @Name is absent
        assert "Production" in data
