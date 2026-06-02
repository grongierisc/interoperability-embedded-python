from unittest.mock import AsyncMock, MagicMock, call

import iris
import pytest

from iop.runtime import director as runtime_director
from iop.runtime.director import _Director


@pytest.fixture
def mock_dispatch():
    """Fixture to mock the dispatchTestComponent method"""
    iris.cls("IOP.Utils").dispatchTestComponent = MagicMock(return_value="test")


class TestDirectorProduction:
    def test_set_default_production(self):
        runtime_director.set_default_production("test")
        glb = iris.gref("^Ens.Configuration")
        result = glb["csp", "LastProduction"]
        assert result == "test"

    def test_get_default_production(self):
        runtime_director.set_default_production("test")
        assert runtime_director.get_default_production() == "test"

    def test_get_default_production_when_not_defined(self):
        runtime_director.set_default_production()
        assert runtime_director.get_default_production() == "Not defined"


class TestDirectorComponent:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup mock for all tests in this class"""
        iris.cls("IOP.Utils").dispatchTestComponent = MagicMock(return_value="test")

    def test_component_with_empty_params(self):
        result = runtime_director.test_component("test")
        assert result == "test"

    def test_component_with_classname(self):
        result = runtime_director.test_component("test", classname="test")
        assert result == "test"

    def test_component_with_iris_classname(self):
        result = runtime_director.test_component(
            "test", classname="iris.Ens.StringRequest"
        )
        assert result == "test"

    def test_component_with_body(self):
        result = runtime_director.test_component("test", classname="test", body="test")
        assert result == "test"

    def test_component_with_iris_classname_and_body(self):
        result = runtime_director.test_component(
            "test", classname="iris.Ens.StringRequest", body="test"
        )
        assert result == "test"

    def test_component_with_nonexistent_iris_classname(self):
        with pytest.raises(RuntimeError):
            runtime_director.test_component("test", classname="iris.test", body="test")


class TestBusinessService:
    def test_get_business_service(self):
        director = _Director()
        iris.cls("IOP.Director").dispatchCreateBusinessService = MagicMock(
            return_value=MagicMock()
        )
        service = director.get_business_service("test")
        assert service is not None

    def test_get_business_service_force_session(self):
        director = _Director()
        mock_service = MagicMock()
        mock_service.iris_handle = MagicMock()
        iris.cls("IOP.Director").dispatchCreateBusinessService = MagicMock(
            return_value=mock_service
        )
        service = director.get_business_service("test", force_session_id=True)
        assert service.iris_handle.ForceSessionId.called

    def test_create_business_service(self):
        iris.cls("IOP.Director").dispatchCreateBusinessService = MagicMock(
            return_value="test"
        )
        result = runtime_director.create_business_service("test")
        assert result == "test"

    def test_create_python_business_service(self):
        mock_obj = MagicMock()
        mock_obj.GetClass = MagicMock(return_value="test_class")
        iris.cls("IOP.Director").dispatchCreateBusinessService = MagicMock(
            return_value=mock_obj
        )
        result = runtime_director.create_python_business_service("test")
        assert result == "test_class"


class TestProductionManagement:
    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        self.start_mock = MagicMock(return_value=iris.system.Status.OK())
        self.stop_mock = MagicMock()
        self.restart_mock = MagicMock()
        self.update_mock = MagicMock()
        self.enable_config_item_mock = MagicMock(return_value=iris.system.Status.OK())
        iris.cls("Ens.Director").StartProduction = self.start_mock
        iris.cls("Ens.Director").StopProduction = self.stop_mock
        iris.cls("Ens.Director").RestartProduction = self.restart_mock
        iris.cls("Ens.Director").UpdateProduction = self.update_mock
        iris.cls("Ens.Director").EnableConfigItem = self.enable_config_item_mock

    def test_start_production(self):
        runtime_director.start_production("test_prod")
        self.start_mock.assert_called_once_with("test_prod")

    def test_start_production_raises_on_status_error(self):
        self.start_mock.return_value = iris.system.Status.Error("start failed")

        with pytest.raises(RuntimeError, match="start failed"):
            runtime_director.start_production("test_prod")

        self.start_mock.assert_called_once_with("test_prod")

    def test_stop_production(self):
        runtime_director.stop_production()
        self.stop_mock.assert_called_once()

    def test_restart_production(self):
        runtime_director.restart_production()
        self.restart_mock.assert_called_once()

    def test_shutdown_production(self):
        runtime_director.shutdown_production()
        self.stop_mock.assert_called_once_with(10, 1)

    def test_update_production(self):
        runtime_director.update_production()
        self.update_mock.assert_called_once()

    def test_start_component(self):
        runtime_director.start_component("Python.Operation")
        self.enable_config_item_mock.assert_called_once_with(
            "Python.Operation",
            1,
            1,
        )

    def test_stop_component(self):
        runtime_director.stop_component("Python.Operation")
        self.enable_config_item_mock.assert_called_once_with(
            "Python.Operation",
            0,
            1,
        )

    def test_restart_component(self):
        runtime_director.restart_component("Python.Operation")
        assert self.enable_config_item_mock.call_args_list == [
            call("Python.Operation", 0, 1),
            call("Python.Operation", 1, 1),
        ]

    def test_list_productions(self):
        iris.cls("IOP.Director").dispatchListProductions = MagicMock(
            return_value=["prod1", "prod2"]
        )
        result = runtime_director.list_productions()
        assert result == ["prod1", "prod2"]

    def test_status_production(self):
        mock_status = {"Production": "test_prod", "Status": "running"}
        iris.cls("IOP.Director").StatusProduction = MagicMock(return_value=mock_status)
        result = runtime_director.status_production()
        assert result == mock_status

    def test_status_production_needs_update(self):
        mock_status = {
            "Production": "test_prod",
            "Status": "running",
            "NeedsUpdate": True,
            "UpdateMessage": "Update available",
        }
        iris.cls("IOP.Director").StatusProduction = MagicMock(return_value=mock_status)
        result = runtime_director.status_production()
        assert result == mock_status


class TestLogging:
    def test_format_log(self):
        test_row = [
            1,
            "Config1",
            "Job1",
            "Msg1",
            "Session1",
            "Source1",
            "Method1",
            "Stack1",
            "Text1",
            "2023-01-01",
            "TraceCat1",
            1,
        ]
        result = runtime_director.format_log(test_row)
        assert "Assert" in result
        assert "Config1" in result

    def test_format_log_different_types(self):
        types = {
            1: "Assert",
            2: "Error",
            3: "Warning",
            4: "Info",
            5: "Trace",
            6: "Alert",
        }
        for type_num, type_str in types.items():
            test_row = [
                1,
                "Config1",
                "Job1",
                "Msg1",
                "Session1",
                "Source1",
                "Method1",
                "Stack1",
                "Text1",
                "2023-01-01",
                "TraceCat1",
                type_num,
            ]
            result = runtime_director.format_log(test_row)
            assert type_str in result

    @pytest.mark.asyncio
    async def test_log_production_async(self):
        handler = AsyncMock()
        handler.sigint_log = True
        await runtime_director._log_production_async(handler)
