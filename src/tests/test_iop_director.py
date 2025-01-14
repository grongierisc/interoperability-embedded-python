import pytest
import iris
from iop._director import _Director
from unittest.mock import MagicMock

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
