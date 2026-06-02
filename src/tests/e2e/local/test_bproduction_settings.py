import os
import sys
import time

from iop import Production
from iop.migration import utils as migration_utils
from iop.runtime.local import _LocalDirector


def _start_for_test(production):
    director = _LocalDirector()
    status = production.status()
    current = status.get("Production") or status.get("production") or ""
    state = str(status.get("Status") or status.get("status") or "").lower()
    if current and current != "Not defined" and state == "running":
        Production(current, director=director).kill()
        for _ in range(30):
            status = director.status_production()
            current = status.get("Production") or status.get("production") or ""
            state = str(status.get("Status") or status.get("status") or "").lower()
            if state != "running":
                break
            time.sleep(1)
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
        path = os.path.join(
            os.path.dirname(__file__), "..", "..", "fixtures", "settings.py"
        )
        migration_utils.migrate(path)
        cls.production = Production.from_dict(
            sys.modules["settings"].TEST_SETTING_PRODUCTION.to_dict(),
            director=_LocalDirector(),
        )
        cls.operation = cls.production.get_component("UnitTest.MySettingOperation")
        _start_for_test(cls.production)

    def test_my_none_var(self):
        rsp = self.operation.test(
            classname="iris.Ens.StringRequest",
            body="my_none_var",
        )
        assert rsp.value is None

    def test_my_str_var(self):
        rsp = self.production.test_component(
            self.operation,
            classname="iris.Ens.StringRequest",
            body="my_str_var",
        )
        assert rsp.value == "bar"

    @classmethod
    def teardown_class(cls):
        try:
            _stop_if_running(cls.production)
        finally:
            Production("test").set_default()
