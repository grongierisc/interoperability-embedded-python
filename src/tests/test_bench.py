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
        # create a list of results
        cls.results = []

    def test_bench_iris(self):
        # this test is made to preload the production
        _Director.test_component('Python.BenchIoPProcess')


    def test_bench_iris_message(self):
        body = "test"
        result = timeit.timeit(lambda: _Director.test_component('Python.BenchIoPProcess','','iris.Ens.StringRequest',body), number=1)
        # set the result in the list
        name = 'Python BP to Python BO with Iris Message'
        self.results.append((name,result))
        # assert the result
        assert result > 0

    def test_bench_iris_message_to_cls(self):
        body = "test"
        result = timeit.timeit(lambda: _Director.test_component('Python.BenchIoPProcess.To.Cls','','iris.Ens.StringRequest',body), number=1)
        # set the result in the list
        name = 'Python BP to ObjetScript BO with Iris Message'
        self.results.append((name,result))
        # assert the result
        assert result > 0

    def test_bench_python_message(self):
        body = "test"
        result = timeit.timeit(lambda: _Director.test_component('Python.BenchIoPProcess','','msg.MyMessage',f'{{"message":"{body}"}}'), number=1)
        # set the result in the list
        name = 'Python BP to Python BO with Python Message'
        self.results.append((name,result))
        # assert the result
        assert result > 0

    def test_bench_python_message_to_cls(self):
        body = "test"
        result = timeit.timeit(lambda: _Director.test_component('Python.BenchIoPProcess.To.Cls','','msg.MyMessage',f'{{"message":"{body}"}}'), number=1)
        # set the result in the list
        name = 'Python BP to ObjetScript BO with Python Message'
        self.results.append((name,result))
        # assert the result
        assert result > 0

    def test_bench_cls_iris_message(self):
        body = "test"
        result = timeit.timeit(lambda: _Director.test_component('Bench.Process','','iris.Ens.StringRequest',body), number=1)
        # set the result in the list
        name = 'ObjetScript BP to Python BO with Iris Message'
        self.results.append((name,result))
        # assert the result
        assert result > 0

    def test_bench_cls_iris_message_to_cls(self):
        body = "test"
        result = timeit.timeit(lambda: _Director.test_component('Bench.Process.To.Cls','','iris.Ens.StringRequest',body), number=1)
        # set the result in the list
        name = 'ObjetScript BP to ObjetScript BO with Iris Message'
        self.results.append((name,result))
        # assert the result
        assert result > 0

    def test_bench_cls_python_message(self):
        body = "test"
        result = timeit.timeit(lambda: _Director.test_component('Bench.Process','','msg.MyMessage',f'{{"message":"{body}"}}'), number=1)
        # set the result in the list
        name = 'ObjetScript BP to Python BO with Python Message'
        self.results.append((name,result))
        # assert the result
        assert result > 0

    def test_bench_cls_python_message_to_cls(self):
        body = "test"
        result = timeit.timeit(lambda: _Director.test_component('Bench.Process.To.Cls','','msg.MyMessage',f'{{"message":"{body}"}}'), number=1)
        # set the result in the list
        name = 'ObjetScript BP to ObjetScript BO with Python Message'
        self.results.append((name,result))
        # assert the result
        assert result > 0

    #after all tests
    @classmethod
    def teardown_class(cls):
        # stop all productions
        _Director.stop_production()
        # set the default production
        _Director.set_default_production('test')
        # write the results in a file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(current_dir,'bench','result.txt'),'w') as f:
            for name,result in cls.results:
                f.write(f'{name}: {result}\n')
