import iris
import os

from grongier.pex._utils import _Utils

def test_filename_to_module():
    # test filename_to_module
    file = 'bo.py'
    result = _Utils.filename_to_module(file)
    expect = 'bo'
    
    assert result == expect

def test_raise_on_error():
    # test raise_on_error
    try:
        sc = iris.system.Status.Error('test')
        _Utils.raise_on_error(sc)
    except RuntimeError as e:
        assert True

def test_setup():
    # test setup
    try:
        _Utils.setup()
    except RuntimeError as e:
        assert False

def test_register_component():
    module = 'bo'
    classname = 'EmailOperation'
    # get the path of the current file
    path = os.path.dirname(os.path.realpath(__file__))
    # join the registerFolder to the path
    path = os.path.join(path, 'registerFiles')
    overwrite = 1
    iris_classname = 'UnitTest.EmailOperation'
    result = _Utils.register_component(module, classname, path, overwrite, iris_classname)
    expect = 1

    assert result == expect

def test_register_folder():
    path = os.path.dirname(os.path.realpath(__file__))
    # join the registerFolder to the path
    path = os.path.join(path, 'registerFiles')
    overwrite = 1
    iris_classname = 'UnitTest.Path'
    result = _Utils.register_folder(path, overwrite, iris_classname)
    expect = None

    assert result == expect

def test_register_file():
    filename = 'bo.py'
    path = os.path.dirname(os.path.realpath(__file__))
    # join the registerFolder to the path
    path = os.path.join(path, 'registerFiles')
    filename = os.path.join(path, filename)
    overwrite = 1
    iris_classname = 'UnitTest.File'
    result = _Utils.register_file(filename, overwrite, iris_classname)
    expect = None

    assert result == expect

def test_register_package():
    package = 'registerFiles'
    path = os.path.dirname(os.path.realpath(__file__))
    overwrite = 1
    iris_classname = 'UnitTest.Package'
    result = _Utils.register_package(package, path, overwrite, iris_classname)
    expect = None

    assert result == expect