# test module for the _director

import iris
import os

from grongier.pex._director import _Director

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