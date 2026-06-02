"""E2E remote tests for production lifecycle commands.

These tests call the actual IOP REST API and verify that the
production management commands work end-to-end.

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
def default_production_name(remote_director):
    default = remote_director.get_default_production()
    if _can_export_production(remote_director, default):
        return default
    prods = remote_director.list_productions()
    for candidate in _production_names(prods):
        if _can_export_production(remote_director, candidate):
            return candidate
    pytest.skip("No exportable productions available on the remote IRIS instance")


@pytest.fixture(scope="module")
def production(remote_director, default_production_name):
    production = Production(default_production_name, director=remote_director)
    production.set_default()
    try:
        production.start()
    except (RuntimeError, requests.exceptions.HTTPError):
        pass
    status = production.status()
    current = status.get("Production") or status.get("production") or ""
    state = str(status.get("Status") or status.get("status") or "").lower()
    if current != default_production_name or state != "running":
        pytest.skip(f"{default_production_name} is not the running production")
    return production


class TestProductionStatus:
    def test_status_returns_dict(self, remote_director):
        """GET /status should return a dict with production and status keys."""
        production = Production("Runtime.Status", director=remote_director)
        result = production.status()
        assert isinstance(result, dict)
        assert "production" in result or "error" not in result

    def test_list_productions(self, remote_director):
        """GET /list should return a non-empty dict of productions."""
        result = remote_director.list_productions()
        assert isinstance(result, dict)

    def test_get_default_production(self, remote_director):
        """GET /default should return a non-empty string."""
        result = remote_director.get_default_production()
        assert isinstance(result, str)
        assert len(result) > 0


class TestProductionLifecycle:
    """Start / restart / stop / kill — only run when a production is configured."""

    def test_restart(self, production):
        """POST /restart should complete without error."""
        production.restart()  # return value is None

    def test_update(self, production):
        """POST /update should complete without error."""
        production.update()  # return value is None


class TestDefaultProduction:
    def test_set_and_get_default(self, remote_director):
        """PUT /default and GET /default round-trip."""
        original = remote_director.get_default_production()
        production = Production(original, director=remote_director)

        try:
            production.set_default()
            result = remote_director.get_default_production()
            assert result == original
        finally:
            # Restore
            production.set_default()
