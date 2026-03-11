import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import json
import os
import tempfile
import requests
from iop._cli import main, _format_test_response
from iop._director import _Director

class TestIOPCli(unittest.TestCase):
    """Test cases for IOP CLI functionality."""

    def test_help_and_basic_commands(self):
        """Test basic CLI commands like help and namespace."""
        # Test help
        with self.assertRaises(SystemExit) as cm:
            main(['-h'])
        self.assertEqual(cm.exception.code, 0)

        # Test without arguments
        with patch('sys.stdout', new=StringIO()) as fake_out:
            with self.assertRaises(SystemExit) as cm:
                main([])
            self.assertEqual(cm.exception.code, 0)
            self.assertIn('Namespace:', fake_out.getvalue())

    def test_namespace_prints_current(self):
        """Test namespace display when no value is provided."""
        with patch.dict(os.environ, {"IRISNAMESPACE": "TESTNS"}, clear=True):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                with self.assertRaises(SystemExit) as cm:
                    main(['-n'])
                self.assertEqual(cm.exception.code, 0)
                self.assertEqual(fake_out.getvalue().strip(), 'TESTNS')

    def test_namespace_with_value_prints_help(self):
        """Test namespace assignment prints help when no other command is provided."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('iop._director._Director.get_default_production') as mock_default:
                mock_default.return_value = 'Bench.Production'
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    with self.assertRaises(SystemExit) as cm:
                        main(['-n', 'MyNS'])
                    self.assertEqual(cm.exception.code, 0)
                    output = fake_out.getvalue()
                    self.assertIn('usage:', output)
                    self.assertIn('Namespace: MyNS', output)

    def test_default_settings(self):
        """Test default production settings."""
        # Test with name
        with self.assertRaises(SystemExit) as cm:
            main(['-d', 'Bench.Production'])
        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(_Director.get_default_production(), 'Bench.Production')

        # Test without name
        with self.assertRaises(SystemExit) as cm:
            main(['-d'])
        self.assertEqual(cm.exception.code, 0)

    def test_production_controls(self):
        """Test production control commands (start, stop, restart, kill)."""
        # Test start
        with patch('iop._director._Director.start_production_with_log') as mock_start:
            with self.assertRaises(SystemExit) as cm:
                main(['-s', 'my_production'])
            self.assertEqual(cm.exception.code, 0)
            mock_start.assert_called_once_with('my_production')

        with patch('iop._director._Director.start_production') as mock_start:
            with self.assertRaises(SystemExit) as cm:
                main(['-s', 'my_production', '-D'])
            self.assertEqual(cm.exception.code, 0)
            mock_start.assert_called_once_with('my_production')

        # Test stop
        with patch('iop._director._Director.stop_production') as mock_stop:
            with patch('sys.stdout', new=StringIO()) as fake_out:
                with self.assertRaises(SystemExit) as cm:
                    main(['-S'])
                self.assertEqual(cm.exception.code, 0)
                mock_stop.assert_called_once()
                self.assertEqual(fake_out.getvalue().strip(), 'Production Bench.Production stopped')

        # Test restart
        with patch('iop._director._Director.restart_production') as mock_restart:
            with self.assertRaises(SystemExit) as cm:
                main(['-r'])
            self.assertEqual(cm.exception.code, 0)
            mock_restart.assert_called_once()

        # Test kill
        with patch('iop._director._Director.shutdown_production') as mock_shutdown:
            with self.assertRaises(SystemExit) as cm:
                main(['-k'])
            self.assertEqual(cm.exception.code, 0)
            mock_shutdown.assert_called_once()

    def test_migration(self):
        """Test migration functionality."""
        # Test relative path
        with patch('iop._utils._Utils.migrate_remote') as mock_migrate:
            with self.assertRaises(SystemExit) as cm:
                main(['-m', 'settings.json'])
            self.assertEqual(cm.exception.code, 0)
            mock_migrate.assert_called_once_with(os.path.join(os.getcwd(), 'settings.json'), force_local=False)

        # Test absolute path
        with patch('iop._utils._Utils.migrate_remote') as mock_migrate:
            with self.assertRaises(SystemExit) as cm:
                main(['-m', '/tmp/settings.json'])
            self.assertEqual(cm.exception.code, 0)
            mock_migrate.assert_called_once_with('/tmp/settings.json', force_local=False)

        # Test with force_local flag
        with patch('iop._utils._Utils.migrate_remote') as mock_migrate:
            with self.assertRaises(SystemExit) as cm:
                main(['-m', '/tmp/settings.json', '--force-local'])
            self.assertEqual(cm.exception.code, 0)
            mock_migrate.assert_called_once_with('/tmp/settings.json', force_local=True)

    def test_status_and_update(self):
        """Test status and update commands."""
        # Test status
        with patch('iop._director._Director.status_production') as mock_status:
            mock_status.return_value = {"Production": "TestProd", "Status": "running"}
            with patch('sys.stdout', new=StringIO()) as fake_out:
                with self.assertRaises(SystemExit) as cm:
                    main(['--status'])
                self.assertEqual(cm.exception.code, 0)
                mock_status.assert_called_once()
                self.assertIn('"Production": "TestProd"', fake_out.getvalue())

        # Test update
        with patch('iop._director._Director.update_production') as mock_update:
            with self.assertRaises(SystemExit) as cm:
                main(['--update'])
            self.assertEqual(cm.exception.code, 0)
            mock_update.assert_called_once()

    def test_initialization(self):
        """Test initialization command."""
        with patch('iop._utils._Utils.setup') as mock_setup:
            with self.assertRaises(SystemExit) as cm:
                main(['-i'])
            self.assertEqual(cm.exception.code, 0)
            mock_setup.assert_called_once_with(None)

    def test_component_testing(self):
        """Test component testing functionality."""
        # _LocalDirector.test_component delegates positionally: (target, message, classname, body)
        # Test with ASCII
        with patch('iop._director._Director.test_component', return_value='ok') as mock_test:
            with self.assertRaises(SystemExit) as cm:
                main(['-t', 'my_test', '-C', 'MyClass', '-B', 'my_body'])
            self.assertEqual(cm.exception.code, 0)
            mock_test.assert_called_once_with('my_test', None, 'MyClass', 'my_body')

        # Test with Unicode
        with patch('iop._director._Director.test_component', return_value='ok') as mock_test:
            with self.assertRaises(SystemExit) as cm:
                main(['-t', 'my_test', '-C', 'MyClass', '-B', 'あいうえお'])
            self.assertEqual(cm.exception.code, 0)
            mock_test.assert_called_once_with('my_test', None, 'MyClass', 'あいうえお')

    def test_component_testing_body_from_file(self):
        """Test that -B @filepath reads body from file."""
        body_data = '{"key": "value"}'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(body_data)
            path = f.name
        try:
            with patch('iop._director._Director.test_component', return_value='ok') as mock_test:
                with self.assertRaises(SystemExit) as cm:
                    main(['-t', 'my_test', '-C', 'MyClass', '-B', f'@{path}'])
                self.assertEqual(cm.exception.code, 0)
                mock_test.assert_called_once_with('my_test', None, 'MyClass', body_data)
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# _format_test_response
# ---------------------------------------------------------------------------

class TestFormatTestResponse(unittest.TestCase):

    def test_dict_with_classname_and_body(self):
        response = {"classname": "Python.MyMsg", "body": '{"key": "value"}'}
        output = _format_test_response(response)
        self.assertIn("classname: Python.MyMsg", output)
        self.assertIn('"key"', output)
        self.assertIn('"value"', output)

    def test_dict_with_error_key(self):
        response = {"error": "Component not found"}
        output = _format_test_response(response)
        self.assertIn("Error: Component not found", output)

    def test_dict_with_truncated_flag(self):
        response = {"classname": "Python.MyMsg", "body": "{}", "truncated": True}
        output = _format_test_response(response)
        self.assertIn("truncated", output)

    def test_dict_empty_returns_str(self):
        response = {}
        output = _format_test_response(response)
        self.assertIsInstance(output, str)

    def test_string_classname_json_pattern(self):
        response = 'Python.MyMsg : {"answer": 42}'
        output = _format_test_response(response)
        self.assertIn("classname: Python.MyMsg", output)
        self.assertIn('"answer"', output)

    def test_string_plain_json(self):
        response = '{"k": "v"}'
        output = _format_test_response(response)
        self.assertIn('"k"', output)

    def test_string_non_json(self):
        response = "plain string response"
        output = _format_test_response(response)
        self.assertEqual(output, "plain string response")

    def test_dataclass_response(self):
        from dataclasses import dataclass
        @dataclass
        class MyMsg:
            message: str = "hello"

        output = _format_test_response(MyMsg(message="world"))
        self.assertIn("world", output)

    def test_arbitrary_object_falls_back_to_str(self):
        class Opaque:
            def __str__(self): return "opaque"
        output = _format_test_response(Opaque())
        self.assertEqual(output, "opaque")


# ---------------------------------------------------------------------------
# Remote mode CLI tests
# ---------------------------------------------------------------------------

class TestCLIRemoteMode(unittest.TestCase):
    """Verify that presence of IOP_URL switches the CLI to _RemoteDirector."""

    _BASE_ENV = {
        "IOP_URL": "http://localhost:8080",
        "IOP_USERNAME": "admin",
        "IOP_PASSWORD": "password",
        "IOP_NAMESPACE": "USER",
    }

    def _mock_resp(self, data):
        resp = MagicMock()
        resp.json.return_value = data
        resp.raise_for_status = MagicMock()
        return resp

    @patch("requests.get")
    def test_status_uses_remote_director(self, mock_get):
        mock_get.return_value = self._mock_resp({"production": "MyProd", "status": "running"})
        with patch.dict(os.environ, self._BASE_ENV, clear=True):
            with patch('sys.stdout', new=StringIO()) as out:
                with self.assertRaises(SystemExit):
                    main(['-x'])
        self.assertIn("running", out.getvalue())
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_list_uses_remote_director(self, mock_get):
        data = {"MyApp.Production": {"Status": "Stopped"}}
        mock_get.return_value = self._mock_resp(data)
        with patch.dict(os.environ, self._BASE_ENV, clear=True):
            with patch('sys.stdout', new=StringIO()) as out:
                with self.assertRaises(SystemExit):
                    main(['-l'])
        self.assertIn("MyApp.Production", out.getvalue())

    @patch("requests.post")
    def test_stop_uses_remote_director(self, mock_post):
        mock_post.return_value = self._mock_resp({"status": "stopped"})
        # get_default_production needs a GET mock too
        with patch("requests.get") as mock_get:
            mock_get.return_value = self._mock_resp({"production": "MyApp.Production"})
            with patch.dict(os.environ, self._BASE_ENV, clear=True):
                with patch('sys.stdout', new=StringIO()):
                    with self.assertRaises(SystemExit):
                        main(['-S'])
        mock_post.assert_called_once()
        args, _ = mock_post.call_args
        self.assertIn("/stop", args[0])

    @patch("requests.post")
    def test_restart_uses_remote_director(self, mock_post):
        mock_post.return_value = self._mock_resp({"status": "restarted"})
        with patch.dict(os.environ, self._BASE_ENV, clear=True):
            with self.assertRaises(SystemExit):
                main(['-r'])
        mock_post.assert_called_once()
        args, _ = mock_post.call_args
        self.assertIn("/restart", args[0])

    @patch("requests.post")
    def test_kill_uses_remote_director(self, mock_post):
        mock_post.return_value = self._mock_resp({"status": "killed"})
        with patch.dict(os.environ, self._BASE_ENV, clear=True):
            with self.assertRaises(SystemExit):
                main(['-k'])
        args, _ = mock_post.call_args
        self.assertIn("/kill", args[0])

    @patch("requests.post")
    def test_update_uses_remote_director(self, mock_post):
        mock_post.return_value = self._mock_resp({"status": "updated"})
        with patch.dict(os.environ, self._BASE_ENV, clear=True):
            with self.assertRaises(SystemExit):
                main(['-u'])
        args, _ = mock_post.call_args
        self.assertIn("/update", args[0])

    @patch("requests.post")
    def test_test_uses_remote_director(self, mock_post):
        mock_post.return_value = self._mock_resp(
            {"classname": "Python.MyMsg", "body": '{"answer": 42}'}
        )
        with patch.dict(os.environ, self._BASE_ENV, clear=True):
            with patch('sys.stdout', new=StringIO()) as out:
                with self.assertRaises(SystemExit):
                    main(['-t', 'Python.MyOp', '-C', 'Python.MyMsg', '-B', '{}'])
        output = out.getvalue()
        self.assertIn("Python.MyMsg", output)
        args, kwargs = mock_post.call_args
        self.assertIn("/test", args[0])
        self.assertEqual(kwargs["json"]["target"], "Python.MyOp")

    @patch("requests.get")
    def test_namespace_flag_overrides_env(self, mock_get):
        mock_get.return_value = self._mock_resp({"production": "P", "status": "running"})
        env = {**self._BASE_ENV, "IOP_NAMESPACE": "USER"}
        with patch.dict(os.environ, env, clear=True):
            with patch('sys.stdout', new=StringIO()):
                with self.assertRaises(SystemExit):
                    main(['-x', '-n', 'MYNS'])
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["namespace"], "MYNS")

    def test_init_warns_in_remote_mode(self):
        env = {**self._BASE_ENV}
        with patch.dict(os.environ, env, clear=True):
            with patch('logging.warning') as mock_warn:
                with self.assertRaises(SystemExit):
                    main(['-i'])
            mock_warn.assert_called_once()
            self.assertIn("local-only", mock_warn.call_args[0][0])

    # ------------------------------------------------------------------
    # --force-local
    # ------------------------------------------------------------------

    @patch("iop._local._Director")
    def test_force_local_bypasses_remote_env(self, mock_director):
        """--force-local must use _LocalDirector even when IOP_URL is set."""
        mock_director.status_production.return_value = {"status": "stopped"}
        env = {**self._BASE_ENV}
        with patch.dict(os.environ, env, clear=True):
            with patch("requests.get") as mock_get:
                with patch('sys.stdout', new=StringIO()):
                    with self.assertRaises(SystemExit):
                        main(['-x', '--force-local'])
                # No HTTP call should have been made
                mock_get.assert_not_called()

    @patch("iop._local._Director")
    def test_force_local_with_migrate(self, mock_director):
        """--force-local should keep migration local even when IOP_URL is set."""
        mock_director.migrate.return_value = None
        content = (
            "REMOTE_SETTINGS = {'url': 'http://remote:8080'}\n"
            "PRODUCTIONS = []\nCLASSES = {}\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            env = {**self._BASE_ENV}
            with patch.dict(os.environ, env, clear=True):
                with patch("requests.post") as mock_post:
                    with patch("iop._utils._Utils.migrate_remote") as mock_migrate:
                        with self.assertRaises(SystemExit):
                            main(['-M', path, '--force-local'])
                        mock_migrate.assert_called_once_with(path, force_local=True)
                    mock_post.assert_not_called()
        finally:
            os.unlink(path)

    # ------------------------------------------------------------------
    # -m settings.py with REMOTE_SETTINGS auto-enables remote mode
    # ------------------------------------------------------------------

    @patch("requests.post")
    def test_migrate_settings_file_remote_settings_enables_remote(self, mock_post):
        """When the settings file has REMOTE_SETTINGS, remote director is used."""
        mock_post.return_value = self._mock_resp({"status": "ok"})
        content = (
            "REMOTE_SETTINGS = {'url': 'http://from-settings:8080',"
            " 'username': 'u', 'password': 'p', 'namespace': 'NS'}\n"
            "PRODUCTIONS = []\nCLASSES = {}\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            # No env vars set — remote mode comes only from the settings file
            with patch.dict(os.environ, {}, clear=True):
                with patch("iop._utils._Utils.migrate_remote") as mock_migrate:
                    with self.assertRaises(SystemExit):
                        main(['-M', path])
                    mock_migrate.assert_called_once()
        finally:
            os.unlink(path)

    # ------------------------------------------------------------------
    # --remote-settings / -R flag
    # ------------------------------------------------------------------

    @patch("requests.get")
    def test_remote_settings_flag_activates_remote_mode(self, mock_get):
        """--remote-settings/-R enables remote mode without any env var."""
        mock_get.return_value = self._mock_resp({"production": "P", "status": "running"})
        content = (
            "REMOTE_SETTINGS = {'url': 'http://flag-file:8080',"
            " 'username': 'u', 'password': 'p', 'namespace': 'USER'}\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            with patch.dict(os.environ, {}, clear=True):
                with patch('sys.stdout', new=StringIO()) as out:
                    with self.assertRaises(SystemExit):
                        main(['-x', '-R', path])
            self.assertIn("running", out.getvalue())
            mock_get.assert_called_once()
            args, _ = mock_get.call_args
            self.assertIn("flag-file:8080", args[0])
        finally:
            os.unlink(path)

    @patch("requests.get")
    def test_remote_settings_short_flag(self, mock_get):
        """Short -R flag works identically to --remote-settings."""
        mock_get.return_value = self._mock_resp({"production": "P", "status": "stopped"})
        content = "REMOTE_SETTINGS = {'url': 'http://short-flag:8080'}\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(SystemExit):
                    main(['-x', '-R', path])
            args, _ = mock_get.call_args
            self.assertIn("short-flag:8080", args[0])
        finally:
            os.unlink(path)

    @patch("requests.get")
    def test_remote_settings_flag_overrides_iop_settings_env(self, mock_get):
        """--remote-settings takes priority over IOP_SETTINGS env var."""
        mock_get.return_value = self._mock_resp({"production": "P", "status": "stopped"})
        file_flag = "REMOTE_SETTINGS = {'url': 'http://flag-wins:8080'}\n"
        file_env = "REMOTE_SETTINGS = {'url': 'http://env-loses:8080'}\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as a:
            a.write(file_flag)
            path_flag = a.name
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as b:
            b.write(file_env)
            path_env = b.name
        try:
            with patch.dict(os.environ, {"IOP_SETTINGS": path_env}, clear=True):
                with self.assertRaises(SystemExit):
                    main(['-x', '-R', path_flag])
            args, _ = mock_get.call_args
            self.assertIn("flag-wins:8080", args[0])
        finally:
            os.unlink(path_flag)
            os.unlink(path_env)

    def test_force_local_overrides_remote_settings_flag(self):
        """--force-local wins over --remote-settings."""
        content = "REMOTE_SETTINGS = {'url': 'http://should-not-use:8080'}\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            with patch.dict(os.environ, {}, clear=True):
                with patch("requests.get") as mock_get:
                    with patch("iop._local._LocalDirector.status_production",
                               return_value={"status": "stopped"}):
                        with self.assertRaises(SystemExit):
                            main(['-x', '-R', path, '--force-local'])
                    mock_get.assert_not_called()
        finally:
            os.unlink(path)

