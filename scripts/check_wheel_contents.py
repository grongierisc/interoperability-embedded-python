#!/usr/bin/env python3
"""Verify that a built wheel contains all packaged IoP support artifacts."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path


def expected_package_files(root: Path) -> set[str]:
    package_root = root / "src" / "iop"
    expected = {"iop/py.typed"}
    expected.update(
        path.relative_to(package_root.parent).as_posix()
        for path in (package_root / "cls").rglob("*.cls")
    )
    return expected


def check_wheel(wheel_path: Path, root: Path) -> None:
    with zipfile.ZipFile(wheel_path) as wheel:
        packaged = set(wheel.namelist())
    missing = sorted(expected_package_files(root) - packaged)
    if missing:
        formatted = "\n".join(f"- {name}" for name in missing)
        raise SystemExit(f"wheel is missing required package files:\n{formatted}")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_wheel_contents.py PATH_TO_WHEEL")
    root = Path(__file__).resolve().parents[1]
    check_wheel(Path(sys.argv[1]).resolve(), root)


if __name__ == "__main__":
    main()
