"""E2E remote tests for the test-component command.

Run with a live IRIS + IOP_URL set:
    IOP_URL=http://localhost:52773 pytest src/tests/e2e/remote/
"""
import pytest
import requests


@pytest.fixture(scope="module")
def default_production(remote_director):
    """Default production name for the configured namespace.

    Falls back to the first production found in the list; skips only when
    no production exists at all.
    """
    prod = remote_director.get_default_production()
    if prod in ("", "Not defined"):
        prods = remote_director.list_productions()
        if not prods:
            pytest.skip("No productions available")
        prod = next(iter(prods))
    return prod


@pytest.fixture(scope="module")
def first_active_component(remote_director, default_production):
    """Name of the first enabled component in the default production, or skip."""
    try:
        remote_director.start_production(default_production)
    except (RuntimeError, requests.exceptions.HTTPError):
        pass  # already running

    components = remote_director.export_production(default_production)
    production_data = list(components.values())[0]
    items = production_data.get("Item", [])
    if isinstance(items, dict):
        items = [items]
    active = [item for item in items if item.get("@Enabled", "1") == "1"]
    if not active:
        pytest.skip("No active components found in the default production")
    return active[0]["@Name"]


class TestComponentTesting:
    def test_test_component_returns_response(self, remote_director, default_production):
        """POST /test with a basic Ens.StringRequest should return a valid response."""
        # Uses Ens.StringRequest as a generic smoke test.
        # Adjust target and classname to match your environment.
        try:
            result = remote_director.test_component(
                target=None,
                classname="Ens.StringRequest",
                body='{"StringValue": "ping"}',
            )
            assert result is not None
        except RuntimeError as exc:
            # If no running target, a RuntimeError is acceptable
            assert "error" in str(exc).lower() or "not found" in str(exc).lower()

    def test_test_component_bad_target_raises(self, remote_director):
        """Sending to a non-existent target should raise RuntimeError."""
        with pytest.raises(RuntimeError):
            remote_director.test_component(
                target="ThisTargetDoesNotExist.AtAll",
                classname="Ens.StringRequest",
                body='{"StringValue": "ping"}',
            )

    def test_test_component_bad_classname_raises(self, remote_director, default_production):
        """Sending with a non-existent classname should raise RuntimeError."""
        with pytest.raises(RuntimeError):
            remote_director.test_component(
                target=None,
                classname="This.Class.DoesNotExist",
                body='{"StringValue": "ping"}',
            )

    def test_test_component_restart(self, remote_director, first_active_component):
        """Test that the restart option in test_component works without error."""
        result = remote_director.test_component(
            target=first_active_component,
            classname=None,
            body='{"StringValue": "ping"}',
            restart=True,
        )
        assert result is not None



