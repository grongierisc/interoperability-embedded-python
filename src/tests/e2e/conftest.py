"""Conftest for all e2e tests.

E2E tests require a running IRIS instance.  The suite is skipped
automatically when IRIS is not available.
"""
import os
import pytest


def _iris_available() -> bool:
    """Return True when the IRIS Python Gateway can be imported and used."""
    if not (os.getenv("IRISINSTALLDIR") or os.getenv("ISC_PACKAGE_INSTALLDIR")):
        return False
    try:
        import iris  # noqa: F401
        return True
    except Exception:
        return False


IRIS_AVAILABLE = _iris_available()

# ── Auto-skip the whole collection when IRIS is absent ─────────────────────

def pytest_collection_modifyitems(config, items):
    skip_e2e = pytest.mark.skip(reason="IRIS not available (set IRISINSTALLDIR or ISC_PACKAGE_INSTALLDIR)")
    for item in items:
        # Skip items that live under e2e/ but NOT under e2e/remote/
        parts = item.nodeid.split("/")
        if "e2e" in parts and "remote" not in parts and not IRIS_AVAILABLE:
            item.add_marker(skip_e2e)
