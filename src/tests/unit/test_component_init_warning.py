import warnings
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from iop.components.business_operation import _BusinessOperation
from iop.components.business_service import _BusinessService

WARNING_TEXT = "instantiates components with __new__() and does not call __init__()"


def _assert_logged_custom_init_warning(component) -> None:
    component.log_warning.assert_called_once()
    message = component.log_warning.call_args.args[0]
    assert WARNING_TEXT in message
    assert "Move startup logic to on_init()" in message
    assert "iop.Setting" in message


def test_custom_init_warns_at_class_definition():
    with pytest.warns(RuntimeWarning, match="instantiates components with __new__"):

        class DefinesInit(_BusinessOperation):
            def __init__(self):
                self.initialized = True


def test_new_dispatch_does_not_call_init_and_logs_warning():
    with pytest.warns(RuntimeWarning, match="instantiates components with __new__"):

        class DefinesInit(_BusinessOperation):
            constructor_called = False
            on_init_called = False

            def __init__(self):
                type(self).constructor_called = True

            def on_init(self):
                type(self).on_init_called = True

    component = DefinesInit.__new__(DefinesInit)
    component.log_warning = MagicMock()

    component._dispatch_on_init(MagicMock())

    assert DefinesInit.constructor_called is False
    assert DefinesInit.on_init_called is True
    _assert_logged_custom_init_warning(component)


def test_component_without_custom_init_does_not_warn_or_log():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")

        class PlainOperation(_BusinessOperation):
            on_init_called = False

            def on_init(self):
                type(self).on_init_called = True

    assert not any(WARNING_TEXT in str(item.message) for item in caught)

    component = PlainOperation.__new__(PlainOperation)
    component.log_warning = MagicMock()

    component._dispatch_on_init(MagicMock())

    assert PlainOperation.on_init_called is True
    component.log_warning.assert_not_called()


def test_inherited_custom_init_warns_and_logs_at_runtime():
    with pytest.warns(RuntimeWarning, match="instantiates components with __new__"):

        class BaseOperation(_BusinessOperation):
            constructor_called = False

            def __init__(self):
                type(self).constructor_called = True

    with pytest.warns(RuntimeWarning, match="instantiates components with __new__"):

        class ChildOperation(BaseOperation):
            pass

    component = ChildOperation.__new__(ChildOperation)
    component.log_warning = MagicMock()

    component._dispatch_on_init(MagicMock())

    assert BaseOperation.constructor_called is False
    _assert_logged_custom_init_warning(component)


def test_decorator_generated_init_is_caught_at_runtime():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")

        @dataclass
        class DataclassOperation(_BusinessOperation):
            value: str = "default"

    assert not any(WARNING_TEXT in str(item.message) for item in caught)

    component = DataclassOperation.__new__(DataclassOperation)
    component.log_warning = MagicMock()

    component._dispatch_on_init(MagicMock())

    _assert_logged_custom_init_warning(component)


def test_metadata_warning_helper_is_safe_for_new_allocated_instances():
    with pytest.warns(RuntimeWarning, match="instantiates components with __new__"):

        class MetadataService(_BusinessService):
            constructor_called = False

            def __init__(self):
                type(self).constructor_called = True

    component = MetadataService.__new__(MetadataService)
    component.log_warning = MagicMock()

    component._warn_if_custom_init()

    assert MetadataService.constructor_called is False
    _assert_logged_custom_init_warning(component)
