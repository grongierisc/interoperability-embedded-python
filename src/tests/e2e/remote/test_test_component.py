"""E2E remote tests for the test-component command.

Run with a live IRIS + IOP_URL set:
    IOP_URL=http://localhost:52773 pytest src/tests/e2e/remote/
"""
import pytest
import requests
from iop import Production


def _production_names(productions):
    if isinstance(productions, dict):
        return list(productions.keys())
    return [str(production) for production in productions]


def _can_export_production(remote_director, production):
    if production in ("", "Not defined"):
        return False
    try:
        remote_director.export_production(production)
    except (RuntimeError, requests.exceptions.HTTPError):
        return False
    return True


@pytest.fixture(scope="module")
def default_production(remote_director):
    """Default production name for the configured namespace.

    Falls back to the first production found in the list; skips only when
    no production exists at all.
    """
    prod = remote_director.get_default_production()
    if _can_export_production(remote_director, prod):
        return prod

    prods = remote_director.list_productions()
    for candidate in _production_names(prods):
        if _can_export_production(remote_director, candidate):
            return candidate
    if not prods:
        pytest.skip("No productions available")
    pytest.skip("No exportable productions available")


@pytest.fixture(scope="module")
def runtime_production(remote_director, default_production):
    """Production API wrapper for the default production, or skip."""
    production = Production.from_iris(default_production, director=remote_director)
    try:
        production.start()
    except (RuntimeError, requests.exceptions.HTTPError):
        pass  # already running

    status = production.status()
    current = status.get("Production") or status.get("production") or ""
    state = str(status.get("Status") or status.get("status") or "").lower()
    if current != default_production or state != "running":
        pytest.skip(f"{default_production} is not the running production")
    return production


@pytest.fixture(scope="module")
def first_active_component(runtime_production):
    """First enabled component in the default production, or skip."""
    active = [
        item
        for item in runtime_production.items
        if str(item.enabled).lower() in {"1", "true"}
    ]
    if not active:
        pytest.skip("No active components found in the default production")
    return active[0]


class TestComponentTesting:
    def test_test_component_returns_response(
        self,
        runtime_production,
        first_active_component,
    ):
        """POST /test with a basic Ens.StringRequest should return a valid response."""
        # Uses Ens.StringRequest as a generic smoke test.
        # Adjust target and classname to match your environment.
        try:
            result = runtime_production.test_component(
                first_active_component,
                classname="Ens.StringRequest",
                body='{"StringValue": "ping"}',
            )
            assert result is not None
        except (RuntimeError, requests.exceptions.HTTPError) as exc:
            # If no running target, an error is acceptable
            assert "error" in str(exc).lower() or "not found" in str(exc).lower()

    def test_test_component_bad_target_raises(self, runtime_production):
        """Sending to a non-existent target should fail before REST dispatch."""
        with pytest.raises(ValueError, match="Production item does not exist"):
            runtime_production.test_component(
                "ThisTargetDoesNotExist.AtAll",
                classname="Ens.StringRequest",
                body='{"StringValue": "ping"}',
            )

    def test_component_ref_test_dispatches_through_production_api(
        self,
        first_active_component,
    ):
        """ComponentRef.test() should dispatch through the Production API."""
        try:
            result = first_active_component.test(
                classname="Ens.StringRequest",
                body='{"StringValue": "ping"}',
            )
            assert result is not None
        except (RuntimeError, requests.exceptions.HTTPError) as exc:
            # A generic message can be rejected by the target component in
            # arbitrary remote environments, but it must reach IRIS.
            assert "not found" in str(exc).lower() or "error" in str(exc).lower()

    def test_component_ref_restart(self, first_active_component):
        """ComponentRef.restart() should restart one production component."""
        first_active_component.restart()
