from iop._director import _Director
from iop._utils import _Utils

import timeit
import os

class TestBenchIoP:

    #before all tests
    @classmethod
    def setup_class(cls):
        # get abspath of 'src/tests/bench'
        path = os.path.abspath('src/tests/bench/settings.py')
        # migrate the production
        _Utils.migrate(path)
        # stop all productions
        _Director.stop_production()
        # set the default production
        _Director.set_default_production('Bench.Production')
        # start the production
        _Director.start_production()

    def test_bench_iris_message(self):
        body = "test"
        result = timeit.timeit(lambda: _Director.test_component('Python.BenchIoPProcess','','iris.Ens.StringRequest',body), number=1)
        # print the time in pytest output
        print(f"Time: {result}")
        # assert the result
        assert result > 0

    def test_bench_python_message(self):
        body = "test"*200000
        result = timeit.timeit(lambda: _Director.test_component('Python.BenchIoPProcess','','msg.MyMessage',f'{{"message":"{body}"}}'), number=1)
        # print the time in pytest output
        print(f"Time: {result}")
        # assert the result
        assert result > 0

    #after all tests
    @classmethod
    def teardown_class(cls):
        # stop all productions
        _Director.stop_production()
        # set the default production
        _Director.set_default_production('test')
