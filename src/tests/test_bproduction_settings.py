from iop._director import _Director
from iop._utils import _Utils

import os

class TestProductionSettings:
    @classmethod
    def setup_class(cls):
        path = 'registerFilesIop/settings.py'
        # get path of the current fille script
        path = os.path.join(os.path.dirname(__file__), path)
        _Utils.migrate(path)
        _Director.stop_production()
        _Director.set_default_production('Python.TestSettingProduction')
        _Director.start_production()

    def test_my_none_var(self):
        rsp = _Director.test_component('UnitTest.MySettingOperation',None,'iris.Ens.StringRequest',"my_none_var")
        assert rsp.value == None

    def test_my_str_var(self):
        rsp = _Director.test_component('UnitTest.MySettingOperation',None,'iris.Ens.StringRequest',"my_str_var")
        assert rsp.value == "bar"


    @classmethod
    def teardown_class(cls):
        _Director.stop_production()
        _Director.set_default_production('test')
