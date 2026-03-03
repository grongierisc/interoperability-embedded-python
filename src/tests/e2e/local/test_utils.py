"""E2E (local IRIS) tests for _Utils."""
import os
import pytest
import iris

from iop._utils import _Utils


@pytest.fixture
def test_path():
    return os.path.dirname(os.path.realpath(__file__))


@pytest.fixture
def register_path(test_path):
    return os.path.join(test_path, '..', '..', 'fixtures')


class TestFileOperations:
    def test_raise_on_error(self):
        with pytest.raises(RuntimeError):
            sc = iris.system.Status.Error('test')
            _Utils.raise_on_error(sc)

    def test_setup_succeeds(self):
        _Utils.setup()


class TestComponentRegistration:
    @pytest.mark.parametrize("module,classname,iris_classname", [
        ('bo', 'EmailOperation', 'UnitTest.EmailOperation'),
        ('bo', 'MyOperation', 'UnitTest.MyOperation'),
    ])
    def test_register_component(self, register_path, module, classname, iris_classname):
        _Utils.register_component(
            module, classname, register_path,
            overwrite=1, iris_classname=iris_classname,
        )


class TestStreamOperations:
    @pytest.mark.parametrize("input_string,expected", [
        ('test', 'test'),
        ('', ''),
        ('test' * 1000, 'test' * 1000),
    ])
    def test_string_stream_conversion(self, input_string, expected):
        stream = _Utils.string_to_stream(input_string)
        result = _Utils.stream_to_string(stream)
        assert result == expected
