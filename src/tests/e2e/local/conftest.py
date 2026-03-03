"""Conftest for local e2e tests.

These tests interact with a running IRIS instance on the local machine.
They are skipped automatically when IRIS is not detected (see e2e/conftest.py).
"""
import sys
from os.path import dirname as d, abspath

# src/tests/ root
_tests_dir = d(d(d(abspath(__file__))))
sys.path.append(d(_tests_dir))           # src/
sys.path.append(_tests_dir)              # src/tests/
sys.path.append(_tests_dir + '/fixtures')  # bare imports inside fixtures/
