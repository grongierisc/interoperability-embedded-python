"""Conftest for unit tests.

Unit tests have zero dependency on a running IRIS instance.
All IRIS calls are mocked via unittest.mock.
"""
import sys
from os.path import dirname as d, abspath

# Inherit root conftest sys.path additions; add unit-test-specific helpers here.
root_dir = d(d(d(abspath(__file__))))   # src/
_tests_dir = d(d(abspath(__file__)))     # src/tests/
sys.path.append(root_dir)
sys.path.append(_tests_dir)
sys.path.append(_tests_dir + '/fixtures')  # bare imports inside fixtures/
