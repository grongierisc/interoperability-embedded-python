import os

import iris
from bench_bo import BenchIoPOperation
from bench_bp import BenchIoPProcess
from msg import MyPersistentMessage

from iop import Production

# get current directory
current_dir = os.path.dirname(os.path.realpath(__file__))
# get working directory
working_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
# get the absolute path of 'src'
src_dir = os.path.abspath(os.path.join(working_dir, os.pardir))

# create a strings with current_dir and src_dir with a | separator
classpaths = f"{current_dir}|{src_dir}"

# load Cos Classes (load source first, then compile in a single pass)
iris.cls("%SYSTEM.OBJ").LoadDir(os.path.join(current_dir, "cls"), "uk", "*.cls", 1)
iris.cls("%SYSTEM.OBJ").Compile("Bench.*", "cb")

BENCH_PRODUCTION = Production(
    "Bench.Production",
    testing_enabled=True,
    actor_pool_size=1,
)
BENCH_PRODUCTION.message("Bench.Msg.MyPersistentMessage", MyPersistentMessage)

bench_operation = BENCH_PRODUCTION.operation(
    "Bench.Operation",
    class_name="Bench.Operation",
)
python_operation = BENCH_PRODUCTION.operation(
    "Python.BenchIoPOperation",
    BenchIoPOperation,
    class_name="Python.BenchIoPOperation",
    settings={"%classpaths": classpaths},
)
python_process = BENCH_PRODUCTION.process(
    "Python.BenchIoPProcess",
    BenchIoPProcess,
    class_name="Python.BenchIoPProcess",
    pool_size=0,
    settings={"%classpaths": classpaths},
)
python_process_to_cls = BENCH_PRODUCTION.process(
    "Python.BenchIoPProcess.To.Cls",
    BenchIoPProcess,
    class_name="Python.BenchIoPProcess",
    pool_size=0,
    settings={"%classpaths": classpaths},
)
bench_process = BENCH_PRODUCTION.process(
    "Bench.Process",
    class_name="Bench.Process",
)
bench_process_to_cls = BENCH_PRODUCTION.process(
    "Bench.Process.To.Cls",
    class_name="Bench.Process",
)

BENCH_PRODUCTION.connect(python_process.target, python_operation)
BENCH_PRODUCTION.connect(python_process_to_cls.target, bench_operation)
BENCH_PRODUCTION.connect(bench_process.port("TargetConfigName"), python_operation)
BENCH_PRODUCTION.connect(bench_process_to_cls.port("TargetConfigName"), bench_operation)

PRODUCTIONS = [BENCH_PRODUCTION]
