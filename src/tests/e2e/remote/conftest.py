"""Conftest for remote e2e tests.

These tests run against a live IRIS instance exposed via its REST API.
They are skipped automatically when IOP_URL is not set.

Required environment variables:
    IOP_URL        e.g. http://localhost:52773
    IOP_USERNAME   e.g. admin
    IOP_PASSWORD   your IRIS password
    IOP_NAMESPACE  default: USER

Or set IOP_SETTINGS pointing to a settings.py with REMOTE_SETTINGS.

Environment variables can also be provided via a .env.remote file at the
project root, which is loaded automatically before the tests run.
"""
import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

from os.path import dirname as d, abspath

# src/tests/ root
_tests_dir = d(d(d(abspath(__file__))))
sys.path.append(d(_tests_dir))           # src/

from iop._remote import get_remote_settings

_ENV_FILE = Path(__file__).parents[4] / ".env.remote"


def pytest_configure(config):
    """Load .env.remote from the project root if it exists."""
    if _ENV_FILE.exists():
        load_dotenv(_ENV_FILE, override=False)


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
