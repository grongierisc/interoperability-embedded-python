from unittest.mock import patch

import pytest

from iop import Director, Utils
from iop.migration.utils import _Utils
from iop.runtime.director import _Director


def test_private_utils_facade_warns_and_delegates():
    with patch("iop.migration.utils.migrate") as migrate:
        with pytest.warns(
            DeprecationWarning,
            match=r"use iop\.migration\.utils\.migrate\(\).*removed in v5\.0",
        ):
            _Utils.migrate("/tmp/settings.py")

    migrate.assert_called_once_with("/tmp/settings.py")


def test_public_utils_facade_warns_and_delegates():
    with patch("iop.migration.utils.register_component") as register_component:
        with pytest.warns(
            DeprecationWarning,
            match=(
                r"use iop\.migration\.utils\.register_component\(\).*"
                r"removed in v5\.0"
            ),
        ):
            Utils.register_component("demo", "Operation", "/tmp")

    register_component.assert_called_once_with("demo", "Operation", "/tmp")


def test_private_director_facade_warns_and_delegates():
    with patch("iop.runtime.director.start_production") as start_production:
        with pytest.warns(
            DeprecationWarning,
            match=r"use iop\.runtime\.director\.start_production\(\).*removed in v5\.0",
        ):
            _Director.start_production("Demo.Production")

    start_production.assert_called_once_with("Demo.Production")


def test_public_director_facade_warns_and_delegates():
    with patch(
        "iop.runtime.director.status_production",
        return_value={"Production": "Demo.Production"},
    ) as status_production:
        with pytest.warns(
            DeprecationWarning,
            match=r"use iop\.runtime\.director\.status_production\(\).*removed in v5\.0",
        ):
            result = Director.status_production()

    status_production.assert_called_once_with()
    assert result == {"Production": "Demo.Production"}
