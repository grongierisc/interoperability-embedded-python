import time
from dataclasses import dataclass
from pathlib import Path

import pytest
from fixtures.teardown_lifecycle_component import TearDownLifecycleService

from iop import Production
from iop.migration import utils as migration_utils
from iop.runtime import director as runtime_director
from iop.runtime.local import _LocalDirector

PRODUCTION_NAME = "Python.TeardownLifecycleProduction"
COMPONENT_NAME = "Python.TeardownLifecycleService"
FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"
SETTINGS_PATH = FIXTURES_DIR / "teardown_lifecycle_settings.py"


@dataclass(frozen=True)
class TeardownRuntimeFiles:
    settings_path: Path
    marker_path: Path


def _production_state(production):
    status = production.status()
    current = status.get("Production") or status.get("production") or ""
    state = str(status.get("Status") or status.get("status") or "").lower()
    return current, state


def _wait_until_not_running(director):
    for _ in range(30):
        status = director.status_production()
        state = str(status.get("Status") or status.get("status") or "").lower()
        if state != "running":
            return
        time.sleep(1)


def _start_for_test(production, director):
    current, state = _production_state(production)
    if current and current != "Not defined" and state == "running":
        Production(current, director=director).kill()
        _wait_until_not_running(director)
    production.set_default()
    production.start()


def _stop_if_running(production):
    current, state = _production_state(production)
    if current == production.name and state == "running":
        production.stop()


@pytest.fixture
def teardown_runtime_files(tmp_path, monkeypatch):
    marker_path = tmp_path / "teardown.marker"
    monkeypatch.setenv("IOP_TEARDOWN_MARKER_PATH", str(marker_path))

    return TeardownRuntimeFiles(
        settings_path=SETTINGS_PATH,
        marker_path=marker_path,
    )


@pytest.fixture
def teardown_production(teardown_runtime_files):
    migration_utils.setup()
    migration_utils.migrate(str(teardown_runtime_files.settings_path))

    director = _LocalDirector()
    production = Production(PRODUCTION_NAME, director=director)
    production.service(
        COMPONENT_NAME,
        TearDownLifecycleService,
        class_name=COMPONENT_NAME,
    )

    try:
        _start_for_test(production, director)
        yield production
    finally:
        _stop_if_running(production)
        Production("test", director=director).set_default()


def test_component_stop_dispatches_teardown_with_host_object(
    teardown_runtime_files,
    teardown_production,
):
    service = runtime_director.create_business_service(COMPONENT_NAME)
    teardown_production.stop_component(COMPONENT_NAME)
    migration_utils.raise_on_error(service.OnTearDown())

    assert teardown_runtime_files.marker_path.read_text(
        encoding="utf-8"
    ) == "torn-down\n"
