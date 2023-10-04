# test module for the _director

import iris

from grongier.pex._director import _Director

from unittest.mock import patch, MagicMock

def test_set_default_production():
    # test set_default_production
    _Director.set_default_production('test')
    glb = iris.gref("^Ens.Configuration")
    result = glb['csp',"LastProduction"]
    assert result == 'test'

def test_get_default_production():
    # test get_default_production
    _Director.set_default_production('test')
    assert _Director.get_default_production() == 'test'

def test_get_default_production_not_defined():
    # test get_default_production
    _Director.set_default_production()
    assert _Director.get_default_production() == 'Not defined'

def test_test_component_empty():
    # use a MagicMock for iris.cls('Grongier.PEX.Utils').dispatchTestComponent 
    iris.cls('Grongier.PEX.Utils').dispatchTestComponent = MagicMock(return_value='test')
    # test test_component
    result = _Director.test_component('test')
    assert result == 'test'

def test_test_component_with_classname():
    # use a MagicMock for iris.cls('Grongier.PEX.Utils').dispatchTestComponent 
    iris.cls('Grongier.PEX.Utils').dispatchTestComponent = MagicMock(return_value='test')
    # test test_component
    result = _Director.test_component('test', classname='test')
    assert result == 'test'

def test_test_component_with_iris_classname():
    # use a MagicMock for iris.cls('Grongier.PEX.Utils').dispatchTestComponent 
    iris.cls('Grongier.PEX.Utils').dispatchTestComponent = MagicMock(return_value='test')
    # test test_component
    result = _Director.test_component('test', classname='iris.Ens.StringRequest')
    assert result == 'test'

def test_test_component_with_body():
    # use a MagicMock for iris.cls('Grongier.PEX.Utils').dispatchTestComponent 
    iris.cls('Grongier.PEX.Utils').dispatchTestComponent = MagicMock(return_value='test')
    # test test_component
    result = _Director.test_component('test',classname='test', body='test')
    assert result == 'test'

def test_test_component_with_iris_classname_and_body():
    # use a MagicMock for iris.cls('Grongier.PEX.Utils').dispatchTestComponent 
    iris.cls('Grongier.PEX.Utils').dispatchTestComponent = MagicMock(return_value='test')
    # test test_component
    result = _Director.test_component('test', classname='iris.Ens.StringRequest', body='test')
    assert result == 'test'

def test_test_component_with_iris_classname_doesnt_exist():
    # use a MagicMock for iris.cls('Grongier.PEX.Utils').dispatchTestComponent 
    iris.cls('Grongier.PEX.Utils').dispatchTestComponent = MagicMock(return_value='test')
    # test test_component
    try:
        result = _Director.test_component('test', classname='iris.test', body='test')
    except RuntimeError as e:
        assert True