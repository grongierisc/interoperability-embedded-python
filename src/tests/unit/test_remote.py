"""Unit tests for iop._remote: _RemoteDirector and get_remote_settings.

No IRIS instance is required — all HTTP calls are mocked.
"""
import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch, call

from iop._remote import _RemoteDirector, get_remote_settings, _print_log_entry, _load_remote_settings_from_file


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE_SETTINGS = {
    "url": "http://localhost:8080",
    "username": "admin",
    "password": "password",
    "namespace": "USER",
    "verify_ssl": True,
}


def _mock_response(json_data, status_code=200):
    """Build a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


def _make_director(**overrides):
    settings = {**BASE_SETTINGS, **overrides}
    return _RemoteDirector(settings)


# ---------------------------------------------------------------------------
# get_remote_settings
# ---------------------------------------------------------------------------

class TestGetRemoteSettings(unittest.TestCase):

    def test_returns_none_when_no_env(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(get_remote_settings())

    def test_from_iop_url_minimal(self):
        env = {"IOP_URL": "http://iris:8080"}
        with patch.dict(os.environ, env, clear=True):
            result = get_remote_settings()
        self.assertIsNotNone(result)
        self.assertEqual(result["url"], "http://iris:8080")
        self.assertEqual(result["username"], "")
        self.assertEqual(result["password"], "")
        self.assertEqual(result["namespace"], "USER")
        self.assertTrue(result["verify_ssl"])

    def test_from_iop_url_full(self):
        env = {
            "IOP_URL": "http://iris:8080",
            "IOP_USERNAME": "admin",
            "IOP_PASSWORD": "secret",
            "IOP_NAMESPACE": "PROD",
            "IOP_VERIFY_SSL": "1",
        }
        with patch.dict(os.environ, env, clear=True):
            result = get_remote_settings()
        self.assertEqual(result["username"], "admin")
        self.assertEqual(result["password"], "secret")
        self.assertEqual(result["namespace"], "PROD")
        self.assertTrue(result["verify_ssl"])

    def test_verify_ssl_false_values(self):
        for falsy in ("0", "false", "False", "FALSE"):
            env = {"IOP_URL": "http://iris:8080", "IOP_VERIFY_SSL": falsy}
            with patch.dict(os.environ, env, clear=True):
                result = get_remote_settings()
            self.assertFalse(result["verify_ssl"], msg=f"Expected False for IOP_VERIFY_SSL={falsy!r}")

    def test_from_iop_settings_file(self):
        content = "REMOTE_SETTINGS = {'url': 'http://from-file:8080', 'namespace': 'TEST'}\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            env = {"IOP_SETTINGS": path}
            with patch.dict(os.environ, env, clear=True):
                result = get_remote_settings()
            self.assertIsNotNone(result)
            self.assertEqual(result["url"], "http://from-file:8080")
            self.assertEqual(result["namespace"], "TEST")
        finally:
            os.unlink(path)

    def test_iop_settings_without_remote_settings_key(self):
        content = "OTHER = 'value'\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            env = {"IOP_SETTINGS": path}
            with patch.dict(os.environ, env, clear=True):
                result = get_remote_settings()
            self.assertIsNone(result)
        finally:
            os.unlink(path)

    def test_iop_url_takes_priority_over_iop_settings(self):
        content = "REMOTE_SETTINGS = {'url': 'http://from-file:8080'}\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            env = {"IOP_URL": "http://from-env:9090", "IOP_SETTINGS": path}
            with patch.dict(os.environ, env, clear=True):
                result = get_remote_settings()
            self.assertEqual(result["url"], "http://from-env:9090")
        finally:
            os.unlink(path)

    def test_bad_settings_file_returns_none(self):
        env = {"IOP_SETTINGS": "/nonexistent/path/settings.py"}
        with patch.dict(os.environ, env, clear=True):
            result = get_remote_settings()
        self.assertIsNone(result)

    # ------------------------------------------------------------------
    # fallback_settings_path (from -m settings.py)
    # ------------------------------------------------------------------

    def test_fallback_settings_path_used_when_no_env(self):
        content = "REMOTE_SETTINGS = {'url': 'http://fallback:8080', 'namespace': 'NS1'}\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            with patch.dict(os.environ, {}, clear=True):
                result = get_remote_settings(fallback_settings_path=path)
            self.assertIsNotNone(result)
            self.assertEqual(result["url"], "http://fallback:8080")
            self.assertEqual(result["namespace"], "NS1")
        finally:
            os.unlink(path)

    def test_iop_url_takes_priority_over_fallback(self):
        content = "REMOTE_SETTINGS = {'url': 'http://fallback:8080'}\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            env = {"IOP_URL": "http://from-env:9090"}
            with patch.dict(os.environ, env, clear=True):
                result = get_remote_settings(fallback_settings_path=path)
            self.assertEqual(result["url"], "http://from-env:9090")
        finally:
            os.unlink(path)

    def test_iop_settings_takes_priority_over_fallback(self):
        file_a = "REMOTE_SETTINGS = {'url': 'http://env-file:8080'}\n"
        file_b = "REMOTE_SETTINGS = {'url': 'http://fallback:8080'}\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as a:
            a.write(file_a)
            path_a = a.name
        with tempfile.NamedTemporaryFile(mode="w", suffix=" .py", delete=False) as b:
            b.write(file_b)
            path_b = b.name
        try:
            env = {"IOP_SETTINGS": path_a}
            with patch.dict(os.environ, env, clear=True):
                result = get_remote_settings(fallback_settings_path=path_b)
            self.assertEqual(result["url"], "http://env-file:8080")
        finally:
            os.unlink(path_a)
            os.unlink(path_b)

    def test_fallback_without_remote_settings_key_returns_none(self):
        content = "CLASSES = {}\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            with patch.dict(os.environ, {}, clear=True):
                result = get_remote_settings(fallback_settings_path=path)
            self.assertIsNone(result)
        finally:
            os.unlink(path)

    def test_fallback_nonexistent_returns_none(self):
        with patch.dict(os.environ, {}, clear=True):
            result = get_remote_settings(fallback_settings_path="/nonexistent.py")
        self.assertIsNone(result)

    # ------------------------------------------------------------------
    # explicit_settings_path (from --remote-settings flag)
    # ------------------------------------------------------------------

    def test_explicit_settings_path_used_when_no_env(self):
        content = "REMOTE_SETTINGS = {'url': 'http://explicit:8080', 'namespace': 'EX'}\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            with patch.dict(os.environ, {}, clear=True):
                result = get_remote_settings(explicit_settings_path=path)
            self.assertIsNotNone(result)
            self.assertEqual(result["url"], "http://explicit:8080")
            self.assertEqual(result["namespace"], "EX")
        finally:
            os.unlink(path)

    def test_explicit_settings_path_takes_priority_over_iop_settings(self):
        file_explicit = "REMOTE_SETTINGS = {'url': 'http://explicit:8080'}\n"
        file_env = "REMOTE_SETTINGS = {'url': 'http://env-file:8080'}\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as a:
            a.write(file_explicit)
            path_explicit = a.name
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as b:
            b.write(file_env)
            path_env = b.name
        try:
            env = {"IOP_SETTINGS": path_env}
            with patch.dict(os.environ, env, clear=True):
                result = get_remote_settings(explicit_settings_path=path_explicit)
            self.assertEqual(result["url"], "http://explicit:8080")
        finally:
            os.unlink(path_explicit)
            os.unlink(path_env)

    def test_explicit_settings_path_takes_priority_over_fallback(self):
        file_explicit = "REMOTE_SETTINGS = {'url': 'http://explicit:8080'}\n"
        file_fallback = "REMOTE_SETTINGS = {'url': 'http://fallback:8080'}\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as a:
            a.write(file_explicit)
            path_explicit = a.name
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as b:
            b.write(file_fallback)
            path_fallback = b.name
        try:
            with patch.dict(os.environ, {}, clear=True):
                result = get_remote_settings(
                    explicit_settings_path=path_explicit,
                    fallback_settings_path=path_fallback,
                )
            self.assertEqual(result["url"], "http://explicit:8080")
        finally:
            os.unlink(path_explicit)
            os.unlink(path_fallback)

    def test_iop_url_still_takes_priority_over_explicit(self):
        content = "REMOTE_SETTINGS = {'url': 'http://explicit:8080'}\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            env = {"IOP_URL": "http://env-url:9090"}
            with patch.dict(os.environ, env, clear=True):
                result = get_remote_settings(explicit_settings_path=path)
            self.assertEqual(result["url"], "http://env-url:9090")
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# _load_remote_settings_from_file
# ---------------------------------------------------------------------------

class TestLoadRemoteSettingsFromFile(unittest.TestCase):

    def test_loads_valid_remote_settings(self):
        content = "REMOTE_SETTINGS = {'url': 'http://host:8080', 'namespace': 'X'}\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            result = _load_remote_settings_from_file(path)
            self.assertIsNotNone(result)
            self.assertEqual(result["url"], "http://host:8080")
        finally:
            os.unlink(path)

    def test_returns_none_when_no_url_key(self):
        content = "REMOTE_SETTINGS = {'username': 'admin'}\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            result = _load_remote_settings_from_file(path)
            self.assertIsNone(result)
        finally:
            os.unlink(path)

    def test_returns_none_for_missing_file(self):
        result = _load_remote_settings_from_file("/does/not/exist.py")
        self.assertIsNone(result)

    def test_returns_none_when_attribute_not_a_dict(self):
        content = "REMOTE_SETTINGS = 'not-a-dict'\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            result = _load_remote_settings_from_file(path)
            self.assertIsNone(result)
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# _RemoteDirector.__init__
# ---------------------------------------------------------------------------

class TestRemoteDirectorInit(unittest.TestCase):

    def test_base_url_strips_trailing_slash(self):
        d = _RemoteDirector({"url": "http://iris:8080/"})
        self.assertEqual(d._base, "http://iris:8080/api/iop")

    def test_auth_defaults(self):
        d = _RemoteDirector({"url": "http://iris:8080"})
        self.assertEqual(d._auth, ("", ""))

    def test_namespace_default(self):
        d = _RemoteDirector({"url": "http://iris:8080"})
        self.assertEqual(d._namespace, "USER")

    def test_verify_ssl_true_by_default(self):
        d = _RemoteDirector({"url": "http://iris:8080"})
        self.assertTrue(d._verify)

    def test_verify_ssl_false_disables_warnings(self):
        import urllib3
        with patch.object(urllib3, "disable_warnings") as mock_dw:
            d = _RemoteDirector({"url": "http://iris:8080", "verify_ssl": False})
            self.assertFalse(d._verify)
            mock_dw.assert_called_once()


# ---------------------------------------------------------------------------
# _check_error
# ---------------------------------------------------------------------------

class TestCheckError(unittest.TestCase):

    def setUp(self):
        self.d = _make_director()

    def test_passthrough_on_non_error(self):
        data = {"production": "MyProd"}
        self.assertEqual(self.d._check_error(data), data)

    def test_raises_on_error_key(self):
        with self.assertRaises(RuntimeError) as ctx:
            self.d._check_error({"error": "something went wrong"})
        self.assertIn("something went wrong", str(ctx.exception))

    def test_passthrough_on_list(self):
        data = [{"id": 1}]
        self.assertEqual(self.d._check_error(data), data)


# ---------------------------------------------------------------------------
# HTTP helpers (_get, _post, _put)
# ---------------------------------------------------------------------------

class TestHttpHelpers(unittest.TestCase):

    def setUp(self):
        self.d = _make_director()

    @patch("requests.get")
    def test_get_includes_namespace(self, mock_get):
        mock_get.return_value = _mock_response({"ok": True})
        self.d._get("/status")
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["namespace"], "USER")

    @patch("requests.get")
    def test_get_merges_extra_params(self, mock_get):
        mock_get.return_value = _mock_response([])
        self.d._get("/log", {"top": 5})
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["top"], 5)
        self.assertEqual(kwargs["params"]["namespace"], "USER")

    @patch("requests.post")
    def test_post_includes_namespace(self, mock_post):
        mock_post.return_value = _mock_response({"status": "ok"})
        self.d._post("/stop")
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["params"]["namespace"], "USER")
        self.assertNotIn("namespace", kwargs["json"])

    @patch("requests.post")
    def test_post_merges_extra_body(self, mock_post):
        mock_post.return_value = _mock_response({"status": "ok"})
        self.d._post("/start", {"production": "MyProd"})
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["production"], "MyProd")

    @patch("requests.put")
    def test_put_includes_namespace(self, mock_put):
        mock_put.return_value = _mock_response({"production": "P"})
        self.d._put("/default", {"production": "P"})
        _, kwargs = mock_put.call_args
        self.assertEqual(kwargs["params"]["namespace"], "USER")
        self.assertNotIn("namespace", kwargs["json"])

    @patch("requests.get")
    def test_get_raises_on_error_status(self, mock_get):
        import requests as _requests
        resp = _mock_response({}, status_code=500)
        resp.ok = False
        resp.reason = "Internal Server Error"
        resp.text = "something went wrong"
        mock_get.return_value = resp
        with self.assertRaises(_requests.exceptions.HTTPError):
            self.d._get("/status")


# ---------------------------------------------------------------------------
# Production lifecycle
# ---------------------------------------------------------------------------

class TestProductionLifecycle(unittest.TestCase):

    def setUp(self):
        self.d = _make_director()

    @patch("requests.get")
    def test_get_default_production(self, mock_get):
        mock_get.return_value = _mock_response({"production": "MyApp.Production"})
        result = self.d.get_default_production()
        self.assertEqual(result, "MyApp.Production")

    @patch("requests.get")
    def test_get_default_production_empty(self, mock_get):
        mock_get.return_value = _mock_response({"production": ""})
        result = self.d.get_default_production()
        self.assertEqual(result, "Not defined")

    @patch("requests.put")
    def test_set_default_production(self, mock_put):
        mock_put.return_value = _mock_response({"production": "NewProd"})
        self.d.set_default_production("NewProd")
        _, kwargs = mock_put.call_args
        self.assertEqual(kwargs["json"]["production"], "NewProd")

    @patch("requests.get")
    def test_list_productions(self, mock_get):
        data = {"MyApp.Production": {"Status": "Running"}}
        mock_get.return_value = _mock_response(data)
        result = self.d.list_productions()
        self.assertEqual(result, data)

    @patch("requests.get")
    def test_status_production(self, mock_get):
        data = {"production": "MyApp.Production", "status": "running"}
        mock_get.return_value = _mock_response(data)
        result = self.d.status_production()
        self.assertEqual(result["status"], "running")

    @patch("requests.get")
    def test_status_production_fills_name_when_missing(self, mock_get):
        # First call returns status with no production name; second returns default
        mock_get.side_effect = [
            _mock_response({"production": "", "status": "stopped"}),
            _mock_response({"production": "Default.Prod"}),
        ]
        result = self.d.status_production()
        self.assertEqual(result["production"], "Default.Prod")

    @patch("requests.post")
    def test_start_production_named(self, mock_post):
        mock_post.return_value = _mock_response({"status": "started"})
        self.d.start_production("MyApp.Production")
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["production"], "MyApp.Production")

    @patch("requests.post")
    def test_start_production_default(self, mock_post):
        mock_post.return_value = _mock_response({"status": "started"})
        self.d.start_production()
        _, kwargs = mock_post.call_args
        self.assertNotIn("production", kwargs["json"])

    @patch("requests.post")
    def test_stop_production(self, mock_post):
        mock_post.return_value = _mock_response({"status": "stopped"})
        self.d.stop_production()
        args, _ = mock_post.call_args
        self.assertIn("/stop", args[0])

    @patch("requests.post")
    def test_shutdown_production(self, mock_post):
        mock_post.return_value = _mock_response({"status": "killed"})
        self.d.shutdown_production()
        args, _ = mock_post.call_args
        self.assertIn("/kill", args[0])

    @patch("requests.post")
    def test_restart_production(self, mock_post):
        mock_post.return_value = _mock_response({"status": "restarted"})
        self.d.restart_production()
        args, _ = mock_post.call_args
        self.assertIn("/restart", args[0])

    @patch("requests.post")
    def test_update_production(self, mock_post):
        mock_post.return_value = _mock_response({"status": "updated"})
        self.d.update_production()
        args, _ = mock_post.call_args
        self.assertIn("/update", args[0])


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

class TestLogging(unittest.TestCase):

    def setUp(self):
        self.d = _make_director()

    def _make_log_entry(self, id=1, text="hello"):
        return {
            "id": id, "config_name": "MyOp", "job": "42", "message_id": "1",
            "session_id": "2", "source_class": "IOP.BusinessOperation",
            "source_method": "OnMessage", "text": text,
            "time_logged": "2026-03-03 10:00:00", "type": "Info",
        }

    @patch("requests.get")
    def test_get_log_entries_top(self, mock_get):
        entries = [self._make_log_entry(i) for i in range(3)]
        mock_get.return_value = _mock_response(entries)
        result = self.d._get_log_entries(top=3)
        self.assertEqual(len(result), 3)
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["top"], 3)

    @patch("requests.get")
    def test_get_log_entries_since_id(self, mock_get):
        mock_get.return_value = _mock_response([self._make_log_entry(10)])
        result = self.d._get_log_entries(since_id=9)
        self.assertEqual(result[0]["id"], 10)
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["since_id"], 9)
        self.assertNotIn("top", kwargs["params"])

    @patch("requests.get")
    def test_get_log_entries_non_list_returns_empty(self, mock_get):
        mock_get.return_value = _mock_response({"error": "some error"})
        # _check_error raises before the isinstance check, so test with valid non-list
        mock_get.return_value = _mock_response("not a list")
        result = self.d._get_log_entries()
        self.assertEqual(result, [])

    @patch("requests.get")
    def test_log_production_top_prints(self, mock_get):
        entries = [self._make_log_entry(1, "msg1"), self._make_log_entry(2, "msg2")]
        mock_get.return_value = _mock_response(entries)
        from io import StringIO
        with patch("builtins.print") as mock_print:
            self.d.log_production_top(top=2)
        self.assertEqual(mock_print.call_count, 2)

    def test_print_log_entry(self):
        entry = self._make_log_entry(1, "test message")
        from io import StringIO
        import sys
        captured = StringIO()
        with patch("sys.stdout", captured):
            _print_log_entry(entry)
        output = captured.getvalue()
        self.assertIn("test message", output)
        self.assertIn("Info", output)


# ---------------------------------------------------------------------------
# test_component
# ---------------------------------------------------------------------------

class TestTestComponent(unittest.TestCase):

    def setUp(self):
        self.d = _make_director()

    @patch("requests.post")
    def test_target_only(self, mock_post):
        mock_post.return_value = _mock_response({"classname": "Ens.Response", "body": "{}"})
        result = self.d.test_component("Python.MyOp")
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["target"], "Python.MyOp")
        self.assertNotIn("classname", kwargs["json"])
        self.assertNotIn("body", kwargs["json"])
        self.assertEqual(result["classname"], "Ens.Response")

    @patch("requests.post")
    def test_with_classname_and_body(self, mock_post):
        mock_post.return_value = _mock_response({"classname": "Python.MyMsg", "body": '{"k":"v"}'})
        result = self.d.test_component("Python.MyOp", classname="Python.MyMsg", body='{"k":"v"}')
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["classname"], "Python.MyMsg")
        self.assertEqual(kwargs["json"]["body"], '{"k":"v"}')

    @patch("requests.post")
    def test_message_arg_is_ignored(self, mock_post):
        """The 'message' positional arg is silently ignored in remote mode."""
        mock_post.return_value = _mock_response({"classname": "", "body": ""})
        self.d.test_component("Python.MyOp", message=object())
        _, kwargs = mock_post.call_args
        self.assertNotIn("message", kwargs["json"])

    @patch("requests.post")
    def test_none_target_sends_empty_string(self, mock_post):
        mock_post.return_value = _mock_response({"classname": "", "body": ""})
        self.d.test_component(None)
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["target"], "")

    @patch("requests.post")
    def test_restart_flag_sent_in_payload(self, mock_post):
        mock_post.return_value = _mock_response({"classname": "Ens.Response", "body": ""})
        self.d.test_component("Python.MyOp", restart=True)
        _, kwargs = mock_post.call_args
        self.assertTrue(kwargs["json"].get("restart"))

    @patch("requests.post")
    def test_restart_true_by_default(self, mock_post):
        mock_post.return_value = _mock_response({"classname": "Ens.Response", "body": ""})
        self.d.test_component("Python.MyOp")
        _, kwargs = mock_post.call_args
        self.assertTrue(kwargs["json"].get("restart"))

    @patch("requests.post")
    def test_restart_false_not_in_payload(self, mock_post):
        mock_post.return_value = _mock_response({"classname": "Ens.Response", "body": ""})
        self.d.test_component("Python.MyOp", restart=False)
        _, kwargs = mock_post.call_args
        self.assertNotIn("restart", kwargs["json"])

    @patch("requests.post")
    def test_error_response_raises(self, mock_post):
        mock_post.return_value = _mock_response({"error": "Component not found"})
        with self.assertRaises(RuntimeError) as ctx:
            self.d.test_component("Python.NonExist")
        self.assertIn("Component not found", str(ctx.exception))


# ---------------------------------------------------------------------------
# export_production
# ---------------------------------------------------------------------------

class TestExportProduction(unittest.TestCase):

    def setUp(self):
        self.d = _make_director()

    @patch("requests.get")
    def test_export_returns_parsed_dict(self, mock_get):
        mock_get.return_value = _mock_response({"MyApp.Production": {"@Name": "MyApp.Production", "Item": []}})
        result = self.d.export_production("MyApp.Production")
        self.assertIsInstance(result, dict)
        self.assertIn("MyApp.Production", result)
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["production"], "MyApp.Production")

    @patch("requests.get")
    def test_export_empty_returns_empty_dict(self, mock_get):
        mock_get.return_value = _mock_response({})
        result = self.d.export_production("MyApp.Production")
        self.assertEqual(result, {})


# ---------------------------------------------------------------------------
# Namespace override
# ---------------------------------------------------------------------------

class TestNamespaceOverride(unittest.TestCase):

    @patch("requests.get")
    def test_custom_namespace_sent_in_params(self, mock_get):
        mock_get.return_value = _mock_response({"production": "P", "status": "running"})
        d = _RemoteDirector({
            "url": "http://iris:8080",
            "namespace": "PRODUCTION",
        })
        d.status_production()
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["namespace"], "PRODUCTION")


if __name__ == "__main__":
    unittest.main()
