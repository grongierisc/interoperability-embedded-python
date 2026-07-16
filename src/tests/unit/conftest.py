"""Small IRIS facade used by unit tests that exercise message serialization."""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from iop.runtime import iris as runtime_iris

TESTS_PATH = Path(__file__).parents[1]
UNIT_IMPORT_PATHS = (TESTS_PATH.parent, TESTS_PATH, TESTS_PATH / "fixtures")
for import_path in UNIT_IMPORT_PATHS:
    path = str(import_path)
    if path not in sys.path:
        sys.path.append(path)


class _FakeStream:
    __module__ = "iris"

    def __init__(self):
        self._value = ""
        self._position = 0

    @property
    def AtEnd(self):
        return self._position >= len(self._value)

    def Rewind(self):
        self._position = 0

    def Read(self, size):
        value = self._value[self._position : self._position + size]
        self._position += len(value)
        return value

    def Write(self, value):
        self._value += value


class _FakeMessage:
    __module__ = "iris"
    buffer = 1_000_000

    def __init__(self, iris_classname="IOP.Message"):
        self._iris_classname = iris_classname
        self.classname = ""
        self._json = ""
        self.type = "String"
        self.jstr = _FakeStream()

    @property
    def json(self):
        return self._json

    @json.setter
    def json(self, value):
        self._json = value
        self.type = "Stream" if isinstance(value, _FakeStream) else "String"

    def _IsA(self, iris_classname):
        return iris_classname == self._iris_classname

    def _Id(self):
        return None


class _FakeClass:
    def __init__(self, iris_classname):
        self._iris_classname = iris_classname

    def _New(self):
        if self._iris_classname == "%Stream.GlobalCharacter":
            return _FakeStream()
        return _FakeMessage(self._iris_classname)

    def __getattr__(self, name):
        return MagicMock(name=f"{self._iris_classname}.{name}")


class _FakeGlobal(dict):
    def __getitem__(self, key):
        return self.get(key)


class _FakeIris:
    def __init__(self):
        self._classes = {}
        self._globals = {}
        self.system = SimpleNamespace(
            Status=SimpleNamespace(
                IsError=lambda status: False,
                GetOneStatusText=lambda status: str(status),
            )
        )
        self.IOP = SimpleNamespace(
            Generator=SimpleNamespace(
                Message=SimpleNamespace(
                    Ack=_FakeClass("IOP.Generator.Message.Ack"),
                    Poll=_FakeClass("IOP.Generator.Message.Poll"),
                    Stop=_FakeClass("IOP.Generator.Message.Stop"),
                )
            )
        )

    def cls(self, iris_classname):
        return self._classes.setdefault(iris_classname, _FakeClass(iris_classname))

    def ref(self):
        return SimpleNamespace(value=None)

    def gref(self, global_name):
        return self._globals.setdefault(global_name, _FakeGlobal())


@pytest.fixture(autouse=True)
def fake_iris_runtime(monkeypatch):
    """Keep unit tests independent from Embedded Python and Native API state."""
    fake_iris = _FakeIris()
    monkeypatch.setattr(runtime_iris, "get_iris", lambda namespace=None: fake_iris)
    return fake_iris
