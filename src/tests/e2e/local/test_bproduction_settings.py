from iop import Production
from iop._local import _LocalDirector
from iop._utils import _Utils

import os
import sys


def _start_for_test(production):
    status = production.status()
    current = status.get("Production") or status.get("production") or ""
    state = str(status.get("Status") or status.get("status") or "").lower()
    if current and current != "Not defined" and state == "running":
        Production(current).stop()
    production.set_default()
    production.start()


def _stop_if_running(production):
    status = production.status()
    current = status.get("Production") or status.get("production") or ""
    state = str(status.get("Status") or status.get("status") or "").lower()
    if current == production.name and state == "running":
        production.stop()


class TestProductionSettings:
    @classmethod
    def setup_class(cls):
        path = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'settings.py')
        _Utils.migrate(path)
        cls.production = Production.from_dict(
            sys.modules["settings"].TEST_SETTING_PRODUCTION.to_dict(),
            director=_LocalDirector(),
        )
        cls.operation = cls.production.get_component("UnitTest.MySettingOperation")
        _start_for_test(cls.production)

    def test_my_none_var(self):
        rsp = self.operation.test(
            classname='iris.Ens.StringRequest',
            body="my_none_var",
        )
        assert rsp.value == None

    def test_my_str_var(self):
        rsp = self.production.test_component(
            self.operation,
            classname='iris.Ens.StringRequest',
            body="my_str_var",
        )
        assert rsp.value == "bar"


    @classmethod
    def teardown_class(cls):
        try:
            _stop_if_running(cls.production)
        finally:
            Production('test').set_default()
