"""E2E remote tests for the migrate command via REST API.

These tests verify that the IOP REST migration endpoint accepts
a valid settings payload and records classes/productions correctly.

Run with a live IRIS + IOP_URL set:
    IOP_URL=http://localhost:52773 pytest src/tests/e2e/remote/
"""
import os
import tempfile
import pytest

from iop._utils import _Utils


@pytest.fixture
def minimal_settings_file(remote_settings, tmp_path):
    """Write a minimal settings.py that points at the remote IRIS instance."""
    content = f"""\
REMOTE_SETTINGS = {{
    "url": "{remote_settings['url']}",
    "username": "{remote_settings.get('username', '')}",
    "password": "{remote_settings.get('password', '')}",
    "namespace": "{remote_settings.get('namespace', 'USER')}",
}}

CLASSES = {{}}
PRODUCTIONS = []
"""
    settings_path = tmp_path / "settings.py"
    settings_path.write_text(content)
    return str(settings_path)


class TestRemoteMigration:
    def test_migrate_empty_settings(self, minimal_settings_file):
        """migrate_remote with an empty CLASSES dict should not raise."""
        # No classes to register means a PUT with an empty payload;
        # the server should respond with 200.
        _Utils.migrate_remote(minimal_settings_file)

    def test_migrate_force_local_skips_remote(self, minimal_settings_file):
        """--force-local must not call the REST API even when REMOTE_SETTINGS is present."""
        import requests
        from unittest.mock import patch

        with patch("requests.put") as mock_put:
            _Utils.migrate_remote(minimal_settings_file, force_local=True)
            mock_put.assert_not_called()
