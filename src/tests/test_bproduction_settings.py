from iop._director import _Director
from iop._utils import _Utils

import os

import iris

class TestProductionSettings:
    @classmethod
    def setup_class(cls):
        path = os.path.join(iris.__getattribute__('__ospath'),'src/tests/registerFilesIop/settings.py')
        _Utils.migrate(path)
        _Director.stop_production()
        _Director.set_default_production('Python.TestSettingProduction')
        _Director.start_production()

    def test_my_none_var(self):
        rsp = _Director.test_component('UnitTest.MySettingOperation',None,'iris.Ens.StringRequest',"my_none_var")
        assert rsp.value == ''

    def test_my_str_var(self):
        rsp = _Director.test_component('UnitTest.MySettingOperation',None,'iris.Ens.StringRequest',"my_str_var")
        assert rsp.value == "bar"


    @classmethod
    def teardown_class(cls):
        _Director.stop_production()
        _Director.set_default_production('test')
