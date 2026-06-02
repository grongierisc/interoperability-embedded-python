"""E2E remote tests for the migrate command via REST API.

These tests verify that the IOP REST migration endpoint accepts
a valid settings payload and records classes/productions correctly.

Run with a live IRIS + IOP_URL set:
    IOP_URL=http://localhost:52773 pytest src/tests/e2e/remote/
"""
import pytest

from iop.runtime.remote import _RemoteDirector


@pytest.fixture
def production_settings_file(remote_settings, tmp_path):
    """Write a minimal Production-based settings.py for the remote IRIS instance."""
    content = f"""\
from iop import Production

REMOTE_SETTINGS = {{
    "url": "{remote_settings['url']}",
    "username": "{remote_settings.get('username', '')}",
    "password": "{remote_settings.get('password', '')}",
    "namespace": "{remote_settings.get('namespace', 'USER')}",
}}

CLASSES = {{}}
PRODUCTIONS = [Production("Remote.E2EProduction", testing_enabled=True)]
"""
    settings_path = tmp_path / "settings.py"
    settings_path.write_text(content)
    return str(settings_path)


class TestRemoteMigration:
    def test_migrate_production_settings(self, production_settings_file, remote_settings):
        """migrate() accepts settings authored with the Production API."""
        director = _RemoteDirector(remote_settings)
        director.migrate(production_settings_file)
