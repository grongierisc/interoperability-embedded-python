from iop._director import _Director
from iop._utils import _Utils
import timeit
import os

class TestBenchIoP:
    TEST_CASES = [
        {
            'name': 'Python BP to Python BO with Iris Message',
            'component': 'Python.BenchIoPProcess',
            'message_type': 'iris.Ens.StringRequest',
            'use_json': False
        },
        {
            'name': 'Python BP to ObjetScript BO with Iris Message',
            'component': 'Python.BenchIoPProcess.To.Cls',
            'message_type': 'iris.Ens.StringRequest',
            'use_json': False
        },
        {
            'name': 'Python BP to Python BO with Python Message',
            'component': 'Python.BenchIoPProcess',
            'message_type': 'msg.MyMessage',
            'use_json': True
        },
        {
            'name': 'Python BP to ObjetScript BO with Python Message',
            'component': 'Python.BenchIoPProcess.To.Cls',
            'message_type': 'msg.MyMessage',
            'use_json': True
        },
        {
            'name': 'Python BP to Python BO with Python Pydantic Message',
            'component': 'Python.BenchIoPProcess',
            'message_type': 'msg.MyPydanticMessage',
            'use_json': True
        },
        {
            'name': 'Python BP to ObjetScript BO with Python Pydantic Message',
            'component': 'Python.BenchIoPProcess.To.Cls',
            'message_type': 'msg.MyPydanticMessage',
            'use_json': True
        },
        {
            'name': 'ObjetScript BP to Python BO with Iris Message',
            'component': 'Bench.Process',
            'message_type': 'iris.Ens.StringRequest',
            'use_json': False
        },
        {
            'name': 'ObjetScript BP to ObjetScript BO with Iris Message',
            'component': 'Bench.Process.To.Cls',
            'message_type': 'iris.Ens.StringRequest',
            'use_json': False
        },
        {
            'name': 'ObjetScript BP to Python BO with Python Message',
            'component': 'Bench.Process',
            'message_type': 'msg.MyMessage',
            'use_json': True
        },
        {
            'name': 'ObjetScript BP to ObjetScript BO with Python Message',
            'component': 'Bench.Process.To.Cls',
            'message_type': 'msg.MyMessage',
            'use_json': True
        },
        {
            'name': 'ObjetScript BP to Python BO with Python Pydantic Message',
            'component': 'Bench.Process',
            'message_type': 'msg.MyPydanticMessage',
            'use_json': True
        },
        {
            'name': 'ObjetScript BP to ObjetScript BO with Python Pydantic Message',
            'component': 'Bench.Process.To.Cls',
            'message_type': 'msg.MyPydanticMessage',
            'use_json': True
        },
        {
            'name': 'Python BP to Python BO with Pickle Message',
            'component': 'Python.BenchIoPProcess',
            'message_type': 'msg.MyPickleMessage',
            'use_json': True
        },
        {
            'name': 'Python BP to ObjetScript BO with Pickle Message',
            'component': 'Python.BenchIoPProcess.To.Cls',
            'message_type': 'msg.MyPickleMessage',
            'use_json': True
        },
        {
            'name': 'ObjetScript BP to Python BO with Pickle Message',
            'component': 'Bench.Process',
            'message_type': 'msg.MyPickleMessage',
            'use_json': True
        },
        {
            'name': 'ObjetScript BP to ObjetScript BO with Pickle Message',
            'component': 'Bench.Process.To.Cls',
            'message_type': 'msg.MyPickleMessage',
            'use_json': True
        },
        {
            'name': 'Python BP to Python BO with Pydantic Pickle Message',
            'component': 'Python.BenchIoPProcess',
            'message_type': 'msg.MyPydanticPickleMessage',
            'use_json': True
        },
        {
            'name': 'Python BP to ObjetScript BO with Pydantic Pickle Message',
            'component': 'Python.BenchIoPProcess.To.Cls',
            'message_type': 'msg.MyPydanticPickleMessage',
            'use_json': True
        },
        {
            'name': 'ObjetScript BP to Python BO with Pydantic Pickle Message',
            'component': 'Bench.Process',
            'message_type': 'msg.MyPydanticPickleMessage',
            'use_json': True
        },
        {
            'name': 'ObjetScript BP to ObjetScript BO with Pydantic Pickle Message',
            'component': 'Bench.Process.To.Cls',
            'message_type': 'msg.MyPydanticPickleMessage',
            'use_json': True
        }
    ]

    @classmethod
    def setup_class(cls):
        path = os.path.abspath('src/tests/bench/settings.py')
        _Utils.migrate(path)
        _Director.stop_production()
        _Director.set_default_production('Bench.Production')
        _Director.start_production()
        cls.results = []

    def test_bench_iris(self):
        _Director.test_component('Python.BenchIoPProcess', '', 'msg.MyMessage', '{"message":"test"}')

    def run_benchmark(self, test_case):
        body = "test"
        message = f'{{"message":"{body}"}}' if test_case['use_json'] else body
        result = timeit.timeit(
            lambda: _Director.test_component(
                test_case['component'],
                '',
                test_case['message_type'],
                message
            ),
            number=1
        )
        self.results.append((test_case['name'], result))
        assert result > 0

    def test_all_benchmarks(self):
        for test_case in self.TEST_CASES:
            self.run_benchmark(test_case)

    @classmethod
    def teardown_class(cls):
        _Director.stop_production()
        _Director.set_default_production('test')
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(current_dir, 'bench', 'result.txt'), 'w') as f:
            for name, result in cls.results:
                f.write(f'{name}: {result}\n')
