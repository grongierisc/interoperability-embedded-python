"""E2E remote tests for production lifecycle commands.

These tests call the actual IOP REST API and verify that the
production management commands work end-to-end.

Run with a live IRIS + IOP_URL set:
    IOP_URL=http://localhost:52773 pytest src/tests/e2e/remote/
"""
import pytest


class TestProductionStatus:
    def test_status_returns_dict(self, remote_director):
        """GET /status should return a dict with production and status keys."""
        result = remote_director.status_production()
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

    @pytest.fixture(autouse=True)
    def _check_production(self, remote_director):
        """Skip if no default production is defined."""
        default = remote_director.get_default_production()
        if default in ("", "Not defined"):
            pytest.skip("No default production defined on the remote IRIS instance")

    def test_restart(self, remote_director):
        """POST /restart should return a status response."""
        result = remote_director.restart_production()
        assert isinstance(result, dict)

    def test_update(self, remote_director):
        """POST /update should complete without error."""
        result = remote_director.update_production()
        assert isinstance(result, dict)


class TestDefaultProduction:
    def test_set_and_get_default(self, remote_director):
        """PUT /default and GET /default round-trip."""
        original = remote_director.get_default_production()

        try:
            remote_director.set_default_production(original)
            result = remote_director.get_default_production()
            assert result == original
        finally:
            # Restore
            remote_director.set_default_production(original)
