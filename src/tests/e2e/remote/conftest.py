"""Conftest for remote e2e tests.

These tests run against a live IRIS instance exposed via its REST API.
They are skipped automatically when IOP_URL is not set.

Required environment variables:
    IOP_URL        e.g. http://localhost:52773
    IOP_USERNAME   e.g. admin
    IOP_PASSWORD   your IRIS password
    IOP_NAMESPACE  default: USER

Or set IOP_SETTINGS pointing to a settings.py with REMOTE_SETTINGS.
"""
import os
import pytest

from iop._remote import get_remote_settings


def pytest_collection_modifyitems(config, items):
    skip_remote = pytest.mark.skip(
        reason="Remote IRIS not configured (set IOP_URL or IOP_SETTINGS)"
    )
    for item in items:
        if "e2e/remote" in item.nodeid.replace(os.sep, "/"):
            if get_remote_settings() is None:
                item.add_marker(skip_remote)


@pytest.fixture(scope="session")
def remote_settings():
    """Session-scoped remote settings dict, or skip the test."""
    settings = get_remote_settings()
    if settings is None:
        pytest.skip("Remote IRIS not configured")
    return settings


@pytest.fixture(scope="session")
def remote_director(remote_settings):
    """A session-scoped _RemoteDirector ready to use."""
    from iop._remote import _RemoteDirector
    return _RemoteDirector(remote_settings)
