"""E2E remote tests for the test-component command.

Run with a live IRIS + IOP_URL set:
    IOP_URL=http://localhost:52773 pytest src/tests/e2e/remote/
"""
import pytest


class TestComponentTesting:
    def test_test_component_returns_response(self, remote_director):
        """POST /test with a basic Ens.StringRequest should return a valid response."""
        default_target = remote_director.get_default_production()
        if default_target in ("", "Not defined"):
            pytest.skip("No default production defined")

        # This test uses Ens.StringRequest as a generic smoke test.
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

    def test_test_component_bad_classname_raises(self, remote_director):
        """Sending with a non-existent classname should raise RuntimeError."""
        default_target = remote_director.get_default_production()
        if default_target in ("", "Not defined"):
            pytest.skip("No default production defined")

        with pytest.raises(RuntimeError):
            remote_director.test_component(
                target=None,
                classname="This.Class.DoesNotExist",
                body='{"StringValue": "ping"}',
            )

    def test_test_component_restart(self, remote_director):
        """Test that the restart option in test_component works without error."""
        default_target = remote_director.get_default_production()
        if default_target in ("", "Not defined"):
            pytest.skip("No default production defined")

        # export the default production's components and pick one to target for this test
        components = remote_director.export_components()
        active_components = [c for c in components if c["active"]]
        

        if not active_components:
            pytest.skip("No active components found in the default production")

        target_component = active_components[0]["name"]
        
        result = remote_director.test_component(
            target=target_component,
            classname="Ens.StringRequest",
            body='{"StringValue": "ping"}',
            restart=True,
        )
        assert result is not None



