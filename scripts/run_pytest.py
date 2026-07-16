"""Run pytest while preserving its exit code under IRIS Embedded Python.

Some preview IRIS builds can change the process status during interpreter
shutdown after pytest has already completed successfully. All pytest fixture
and plugin teardown has finished by the time ``pytest.main`` returns, so exit
directly with that result instead of allowing a later runtime hook to replace
it.
"""

from __future__ import annotations

import os
import sys

import pytest


def main() -> None:
    exit_code = pytest.main(sys.argv[1:])
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(int(exit_code))


if __name__ == "__main__":
    main()
