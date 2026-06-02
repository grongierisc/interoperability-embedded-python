"""Unit tests for iop.runtime.local._LocalDirector.

Verifies that every method correctly delegates to _Director or migration_utils.
No IRIS instance required — all underlying calls are mocked.
"""

import unittest
from unittest.mock import MagicMock, patch

from iop.messages.serialization import MessageClassImportError
from iop.runtime import director as runtime_director
from iop.runtime.local import _LocalDirector


class FakeTestResponse:
    def __init__(self, classname, body, is_iop_message=True):
        self.classname = classname
        self.json = body
        self.jstr = "pickle body should not be used"
        self.type = "String"
        self._is_iop_message = is_iop_message

    def _IsA(self, classname):
        return classname == "IOP.Message" and self._is_iop_message


class FakeIris:
    def __init__(self, response):
        self.utils = MagicMock()
        self.utils.dispatchTestComponent.return_value = response

    def cls(self, classname):
        if classname == "IOP.Utils":
            return self.utils
        raise AssertionError(f"Unexpected IRIS class lookup: {classname}")


class TestLocalDirectorDelegation(unittest.TestCase):
    """Each _LocalDirector method must delegate to the matching _Director static."""

    def setUp(self):
        self.d = _LocalDirector()

    # ------------------------------------------------------------------
    # Default production
    # ------------------------------------------------------------------

    @patch("iop.runtime.director.get_default_production", return_value="MyProd")
    def test_get_default_production(self, mock):
        result = self.d.get_default_production()
        mock.assert_called_once_with()
        self.assertEqual(result, "MyProd")

    @patch("iop.runtime.director.set_default_production")
    def test_set_default_production(self, mock):
        self.d.set_default_production("NewProd")
        mock.assert_called_once_with("NewProd")

    @patch("iop.runtime.director.set_default_production")
    def test_set_default_production_empty(self, mock):
        self.d.set_default_production()
        mock.assert_called_once_with("")

    # ------------------------------------------------------------------
    # List / status
    # ------------------------------------------------------------------

    @patch("iop.runtime.director.list_productions", return_value={"A": {}})
    def test_list_productions(self, mock):
        result = self.d.list_productions()
        mock.assert_called_once_with()
        self.assertEqual(result, {"A": {}})

    @patch("iop.runtime.director.status_production", return_value={"status": "running"})
    def test_status_production(self, mock):
        result = self.d.status_production()
        mock.assert_called_once_with()
        self.assertEqual(result["status"], "running")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @patch("iop.runtime.director.start_production")
    def test_start_production(self, mock):
        self.d.start_production("MyProd")
        mock.assert_called_once_with("MyProd")

    @patch("iop.runtime.director.start_production_with_log")
    def test_start_production_with_log(self, mock):
        self.d.start_production_with_log("MyProd")
        mock.assert_called_once_with("MyProd")

    @patch("iop.runtime.director.stop_production")
    def test_stop_production(self, mock):
        self.d.stop_production()
        mock.assert_called_once_with()

    @patch("iop.runtime.director.shutdown_production")
    def test_shutdown_production(self, mock):
        self.d.shutdown_production()
        mock.assert_called_once_with()

    @patch("iop.runtime.director.restart_production")
    def test_restart_production(self, mock):
        self.d.restart_production()
        mock.assert_called_once_with()

    @patch("iop.runtime.director.update_production")
    def test_update_production(self, mock):
        self.d.update_production()
        mock.assert_called_once_with()

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    @patch("iop.runtime.director.log_production_top")
    def test_log_production_top(self, mock):
        self.d.log_production_top(25)
        mock.assert_called_once_with(25)

    @patch("iop.runtime.director.log_production")
    def test_log_production(self, mock):
        self.d.log_production()
        mock.assert_called_once_with()

    # ------------------------------------------------------------------
    # Test component
    # ------------------------------------------------------------------

    @patch("iop.runtime.director.test_component", return_value="response")
    def test_test_component_minimal(self, mock):
        result = self.d.test_component("Python.MyOp")
        mock.assert_called_once_with("Python.MyOp", None, None, None)
        self.assertEqual(result, "response")

    @patch("iop.runtime.director.test_component", return_value="response")
    def test_test_component_full(self, mock):
        msg = object()
        result = self.d.test_component(
            "Python.MyOp", message=msg, classname="Python.MyMsg", body='{"k":"v"}'
        )
        mock.assert_called_once_with("Python.MyOp", msg, "Python.MyMsg", '{"k":"v"}')
        self.assertEqual(result, "response")

    def test_test_component_returns_raw_json_when_response_class_is_not_importable(self):
        response = FakeTestResponse(
            classname="hello_world.msg.MyMsg",
            body='{"greeting": "hello"}',
        )
        iris = FakeIris(response)

        with (
            patch.object(runtime_director._iris, "get_iris", return_value=iris),
            patch.object(runtime_director, "dispatch_serializer", return_value="serial"),
            patch.object(
                runtime_director,
                "dispatch_deserializer",
                side_effect=MessageClassImportError("missing class"),
            ),
        ):
            result = runtime_director.test_component("Python.MyOp", message=object())

        iris.utils.dispatchTestComponent.assert_called_once_with("Python.MyOp", "serial")
        self.assertEqual(
            result,
            {
                "classname": "hello_world.msg.MyMsg",
                "body": '{"greeting": "hello"}',
                "truncated": False,
            },
        )

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    @patch(
        "iop.migration.utils.export_production", return_value='{"MyApp.Production": {}}'
    )
    def test_export_production(self, mock):
        result = self.d.export_production("MyApp.Production")
        mock.assert_called_once_with("MyApp.Production")
        self.assertEqual(result, {"MyApp.Production": {}})


if __name__ == "__main__":
    unittest.main()
