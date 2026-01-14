import pytest
import iris
from iop._director import _Director
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_dispatch():
    """Fixture to mock the dispatchTestComponent method"""
    iris.cls('IOP.Utils').dispatchTestComponent = MagicMock(return_value='test')

class TestDirectorProduction:
    def test_set_default_production(self):
        _Director.set_default_production('test')
        glb = iris.gref("^Ens.Configuration")
        result = glb['csp',"LastProduction"]
        assert result == 'test'

    def test_get_default_production(self):
        _Director.set_default_production('test')
        assert _Director.get_default_production() == 'test'

    def test_get_default_production_when_not_defined(self):
        _Director.set_default_production()
        assert _Director.get_default_production() == 'Not defined'

class TestDirectorComponent:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup mock for all tests in this class"""
        iris.cls('IOP.Utils').dispatchTestComponent = MagicMock(return_value='test')

    def test_component_with_empty_params(self):
        result = _Director.test_component('test')
        assert result == 'test'

    def test_component_with_classname(self):
        result = _Director.test_component('test', classname='test')
        assert result == 'test'

    def test_component_with_iris_classname(self):
        result = _Director.test_component('test', classname='iris.Ens.StringRequest')
        assert result == 'test'

    def test_component_with_body(self):
        result = _Director.test_component('test', classname='test', body='test')
        assert result == 'test'

    def test_component_with_iris_classname_and_body(self):
        result = _Director.test_component('test', classname='iris.Ens.StringRequest', body='test')
        assert result == 'test'

    def test_component_with_nonexistent_iris_classname(self):
        with pytest.raises(RuntimeError):
            _Director.test_component('test', classname='iris.test', body='test')

class TestBusinessService:
    def test_get_business_service(self):
        director = _Director()
        iris.cls("IOP.Director").dispatchCreateBusinessService = MagicMock(return_value=MagicMock())
        service = director.get_business_service("test")
        assert service is not None
        
    def test_get_business_service_force_session(self):
        director = _Director()
        mock_service = MagicMock()
        mock_service.iris_handle = MagicMock()
        iris.cls("IOP.Director").dispatchCreateBusinessService = MagicMock(return_value=mock_service)
        service = director.get_business_service("test", force_session_id=True)
        assert service.iris_handle.ForceSessionId.called

    def test_create_business_service(self):
        iris.cls("IOP.Director").dispatchCreateBusinessService = MagicMock(return_value="test")
        result = _Director.create_business_service("test")
        assert result == "test"

    def test_create_python_business_service(self):
        mock_obj = MagicMock()
        mock_obj.GetClass = MagicMock(return_value="test_class")
        iris.cls("IOP.Director").dispatchCreateBusinessService = MagicMock(return_value=mock_obj)
        result = _Director.create_python_business_service("test")
        assert result == "test_class"

class TestProductionManagement:
    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        self.start_mock = MagicMock()
        self.stop_mock = MagicMock()
        self.restart_mock = MagicMock()
        self.update_mock = MagicMock()
        iris.cls('Ens.Director').StartProduction = self.start_mock
        iris.cls('Ens.Director').StopProduction = self.stop_mock
        iris.cls('Ens.Director').RestartProduction = self.restart_mock
        iris.cls('Ens.Director').UpdateProduction = self.update_mock

    def test_start_production(self):
        _Director.start_production("test_prod")
        self.start_mock.assert_called_once_with("test_prod")

    def test_stop_production(self):
        _Director.stop_production()
        self.stop_mock.assert_called_once()

    def test_restart_production(self):
        _Director.restart_production()
        self.restart_mock.assert_called_once()

    def test_shutdown_production(self):
        _Director.shutdown_production()
        self.stop_mock.assert_called_once_with(10, 1)

    def test_update_production(self):
        _Director.update_production()
        self.update_mock.assert_called_once()

    def test_list_productions(self):
        iris.cls('IOP.Director').dispatchListProductions = MagicMock(return_value=["prod1", "prod2"])
        result = _Director.list_productions()
        assert result == ["prod1", "prod2"]

    def test_status_production(self):
        mock_status = {'Production': 'test_prod', 'Status': 'running'}
        iris.cls('IOP.Director').StatusProduction = MagicMock(return_value=mock_status)
        result = _Director.status_production()
        assert result == mock_status

    def test_status_production_needs_update(self):
        mock_status = {
            'Production': 'test_prod', 
            'Status': 'running',
            'NeedsUpdate': True,
            'UpdateMessage': 'Update available'
        }
        iris.cls('IOP.Director').StatusProduction = MagicMock(return_value=mock_status)
        result = _Director.status_production()
        assert result == mock_status

class TestLogging:
    def test_format_log(self):
        test_row = [1, 'Config1', 'Job1', 'Msg1', 'Session1', 'Source1', 'Method1', 
                    'Stack1', 'Text1', '2023-01-01', 'TraceCat1', 1]
        result = _Director.format_log(test_row)
        assert 'Assert' in result
        assert 'Config1' in result

    def test_format_log_different_types(self):
        types = {1: 'Assert', 2: 'Error', 3: 'Warning', 4: 'Info', 5: 'Trace', 6: 'Alert'}
        for type_num, type_str in types.items():
            test_row = [1, 'Config1', 'Job1', 'Msg1', 'Session1', 'Source1', 'Method1',
                       'Stack1', 'Text1', '2023-01-01', 'TraceCat1', type_num]
            result = _Director.format_log(test_row)
            assert type_str in result

    @pytest.mark.asyncio
    async def test_log_production_async(self):
        handler = AsyncMock()
        handler.sigint_log = True
        await _Director._log_production_async(handler)
