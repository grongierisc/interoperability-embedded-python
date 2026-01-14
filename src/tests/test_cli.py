import unittest
from unittest.mock import patch
from io import StringIO
import json
import os
from iop._cli import main
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

    def test_default_settings(self):
        """Test default production settings."""
        # Test with name
        with self.assertRaises(SystemExit) as cm:
            main(['-d', 'UnitTest.Production'])
        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(_Director.get_default_production(), 'UnitTest.Production')

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
                self.assertEqual(fake_out.getvalue().strip(), 'Production UnitTest.Production stopped')

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
        # Test with ASCII
        with patch('iop._director._Director.test_component') as mock_test:
            with self.assertRaises(SystemExit) as cm:
                main(['-t', 'my_test', '-C', 'MyClass', '-B', 'my_body'])
            self.assertEqual(cm.exception.code, 0)
            mock_test.assert_called_once_with('my_test', classname='MyClass', body='my_body')

        # Test with Unicode
        with patch('iop._director._Director.test_component') as mock_test:
            with self.assertRaises(SystemExit) as cm:
                main(['-t', 'my_test', '-C', 'MyClass', '-B', 'あいうえお'])
            self.assertEqual(cm.exception.code, 0)
            mock_test.assert_called_once_with('my_test', classname='MyClass', body='あいうえお')
