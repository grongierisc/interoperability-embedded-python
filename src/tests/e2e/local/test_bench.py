from iop import Production
from iop.runtime.local import _LocalDirector
from iop.migration.utils import _Utils
import sys
import os
import timeit


def _start_for_test(production):
    status = production.status()
    current = status.get("Production") or status.get("production") or ""
    state = str(status.get("Status") or status.get("status") or "").lower()
    if current and current != "Not defined" and state == "running":
        Production(current).stop()
    production.set_default()
    production.start()


def _stop_if_running(production):
    status = production.status()
    current = status.get("Production") or status.get("production") or ""
    state = str(status.get("Status") or status.get("status") or "").lower()
    if current == production.name and state == "running":
        production.stop()


class TestBenchIoP:
    TEST_CASES = [
        {
            "name": "Python BP to Python BO with Iris Message",
            "component": "Python.BenchIoPProcess",
            "message_type": "iris.Ens.StringRequest",
            "use_json": False,
        },
        {
            "name": "Python BP to ObjetScript BO with Iris Message",
            "component": "Python.BenchIoPProcess.To.Cls",
            "message_type": "iris.Ens.StringRequest",
            "use_json": False,
        },
        {
            "name": "Python BP to Python BO with Python Message",
            "component": "Python.BenchIoPProcess",
            "message_type": "msg.MyMessage",
            "use_json": True,
        },
        {
            "name": "Python BP to ObjetScript BO with Python Message",
            "component": "Python.BenchIoPProcess.To.Cls",
            "message_type": "msg.MyMessage",
            "use_json": True,
        },
        {
            "name": "Python BP to Python BO with Python Pydantic Message",
            "component": "Python.BenchIoPProcess",
            "message_type": "msg.MyPydanticMessage",
            "use_json": True,
        },
        {
            "name": "Python BP to ObjetScript BO with Python Pydantic Message",
            "component": "Python.BenchIoPProcess.To.Cls",
            "message_type": "msg.MyPydanticMessage",
            "use_json": True,
        },
        {
            "name": "Python BP to Python BO with Persistent Message",
            "component": "Python.BenchIoPProcess",
            "message_type": "msg.MyPersistentMessage",
            "persistent": True,
        },
        {
            "name": "Python BP to ObjetScript BO with Persistent Message",
            "component": "Python.BenchIoPProcess.To.Cls",
            "message_type": "msg.MyPersistentMessage",
            "persistent": True,
        },
        {
            "name": "ObjetScript BP to Python BO with Iris Message",
            "component": "Bench.Process",
            "message_type": "iris.Ens.StringRequest",
            "use_json": False,
        },
        {
            "name": "ObjetScript BP to ObjetScript BO with Iris Message",
            "component": "Bench.Process.To.Cls",
            "message_type": "iris.Ens.StringRequest",
            "use_json": False,
        },
        {
            "name": "ObjetScript BP to Python BO with Python Message",
            "component": "Bench.Process",
            "message_type": "msg.MyMessage",
            "use_json": True,
        },
        {
            "name": "ObjetScript BP to ObjetScript BO with Python Message",
            "component": "Bench.Process.To.Cls",
            "message_type": "msg.MyMessage",
            "use_json": True,
        },
        {
            "name": "ObjetScript BP to Python BO with Python Pydantic Message",
            "component": "Bench.Process",
            "message_type": "msg.MyPydanticMessage",
            "use_json": True,
        },
        {
            "name": "ObjetScript BP to ObjetScript BO with Python Pydantic Message",
            "component": "Bench.Process.To.Cls",
            "message_type": "msg.MyPydanticMessage",
            "use_json": True,
        },
        {
            "name": "ObjetScript BP to Python BO with Persistent Message",
            "component": "Bench.Process",
            "message_type": "msg.MyPersistentMessage",
            "persistent": True,
        },
        {
            "name": "ObjetScript BP to ObjetScript BO with Persistent Message",
            "component": "Bench.Process.To.Cls",
            "message_type": "msg.MyPersistentMessage",
            "persistent": True,
        },
        {
            "name": "Python BP to Python BO with Pickle Message",
            "component": "Python.BenchIoPProcess",
            "message_type": "msg.MyPickleMessage",
            "use_json": True,
        },
        {
            "name": "Python BP to ObjetScript BO with Pickle Message",
            "component": "Python.BenchIoPProcess.To.Cls",
            "message_type": "msg.MyPickleMessage",
            "use_json": True,
        },
        {
            "name": "ObjetScript BP to Python BO with Pickle Message",
            "component": "Bench.Process",
            "message_type": "msg.MyPickleMessage",
            "use_json": True,
        },
        {
            "name": "ObjetScript BP to ObjetScript BO with Pickle Message",
            "component": "Bench.Process.To.Cls",
            "message_type": "msg.MyPickleMessage",
            "use_json": True,
        },
        {
            "name": "Python BP to Python BO with Pydantic Pickle Message",
            "component": "Python.BenchIoPProcess",
            "message_type": "msg.MyPydanticPickleMessage",
            "use_json": True,
        },
        {
            "name": "Python BP to ObjetScript BO with Pydantic Pickle Message",
            "component": "Python.BenchIoPProcess.To.Cls",
            "message_type": "msg.MyPydanticPickleMessage",
            "use_json": True,
        },
        {
            "name": "ObjetScript BP to Python BO with Pydantic Pickle Message",
            "component": "Bench.Process",
            "message_type": "msg.MyPydanticPickleMessage",
            "use_json": True,
        },
        {
            "name": "ObjetScript BP to ObjetScript BO with Pydantic Pickle Message",
            "component": "Bench.Process.To.Cls",
            "message_type": "msg.MyPydanticPickleMessage",
            "use_json": True,
        },
    ]

    @classmethod
    def setup_class(cls):
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "bench", "settings.py"
        )
        _Utils.migrate(path)
        cls.production = Production.from_dict(
            sys.modules["settings"].BENCH_PRODUCTION.to_dict(),
            director=_LocalDirector(),
        )
        _start_for_test(cls.production)
        cls.persistent_message_cls = sys.modules["settings"].MyPersistentMessage
        cls.results = []

    def test_bench_iris(self):
        self.production.test_component(
            "Python.BenchIoPProcess",
            classname="msg.MyMessage",
            body='{"message":"test"}',
        )

    def run_benchmark(self, test_case):
        body = "test"
        if test_case.get("persistent"):
            message = self.persistent_message_cls(message=body)
            classname = None
            payload = None
        else:
            message = None
            classname = test_case["message_type"]
            payload = f'{{"message":"{body}"}}' if test_case["use_json"] else body

        result = timeit.timeit(
            lambda: self.production.test_component(
                test_case["component"],
                message=message,
                classname=classname,
                body=payload,
            ),
            number=1,
        )
        self.results.append((test_case["name"], result))
        assert result > 0

    def test_all_benchmarks(self):
        for test_case in self.TEST_CASES:
            self.run_benchmark(test_case)

    @classmethod
    def teardown_class(cls):
        try:
            _stop_if_running(cls.production)
        finally:
            Production("test").set_default()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(current_dir, "bench", "result.txt"), "w") as f:
            for name, result in cls.results:
                f.write(f"{name}: {result}\n")
