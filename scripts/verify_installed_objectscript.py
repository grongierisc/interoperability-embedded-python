#!/usr/bin/env python3
"""Compile packaged ObjectScript and verify every source class is installed."""

from __future__ import annotations

import re
from collections.abc import Iterator
from importlib.resources import files
from importlib.resources.abc import Traversable

import iris

from iop.migration.utils import setup

CLASS_DECLARATION = re.compile(r"^Class\s+([%A-Za-z][%A-Za-z0-9.]*)\b", re.MULTILINE)


def _class_resources(root: Traversable) -> Iterator[Traversable]:
    for resource in root.iterdir():
        if resource.is_dir():
            yield from _class_resources(resource)
        elif resource.name.endswith(".cls"):
            yield resource


def packaged_class_names() -> set[str]:
    names: set[str] = set()
    root = files("iop").joinpath("cls")
    for resource in _class_resources(root):
        match = CLASS_DECLARATION.search(resource.read_text(encoding="utf-8"))
        if match is None:
            raise RuntimeError(f"no class declaration found in {resource}")
        names.add(match.group(1))
    return names


def installed_class_names() -> set[str]:
    rows = iris.sql.exec(
        "SELECT Name FROM %Dictionary.ClassDefinition WHERE Name %STARTSWITH 'IOP.'"
    )
    return {str(row[0]) for row in rows}


def main() -> None:
    expected = packaged_class_names()
    setup()
    missing = sorted(expected - installed_class_names())
    if missing:
        formatted = "\n".join(f"- {name}" for name in missing)
        raise SystemExit(f"packaged ObjectScript classes were not installed:\n{formatted}")
    print(f"Verified {len(expected)} packaged ObjectScript classes.")


if __name__ == "__main__":
    main()
