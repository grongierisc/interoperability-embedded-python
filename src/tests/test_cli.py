import unittest
from unittest.mock import patch
from io import StringIO
import json
import os
from grongier.pex._cli import main
from iop._director import _Director

def test_help():
    # test help
    try:
        main(['-h'])
    except SystemExit as e:
        assert e.code == 0

def test_default_with_name():
    # test default
    try:
        main(['-d', 'UnitTest.Production'])
    except SystemExit as e:
        assert e.code == 0
        # assert the output
        assert _Director.get_default_production() == 'UnitTest.Production'

def test_default_without_name():
    # test default
    try:
        main(['-d'])
    except SystemExit as e:
        assert e.code == 0

def test_cli_namespace():
    try:
        main([])
    except SystemExit as e:
        assert e.code == 0

def test_start():
    with patch('grongier.pex._director._Director.start_production_with_log') as mock_start:
        try:
            main(['-s', 'my_production'])
        except SystemExit as e:
            assert e.code == 0
        mock_start.assert_called_once_with('my_production')
    with patch('grongier.pex._director._Director.start_production') as mock_start:
        try:
            main(['-s', 'my_production', '-D'])
        except SystemExit as e:
            assert e.code == 0
        mock_start.assert_called_once_with('my_production')

def test_init():
    with patch('grongier.pex._utils._Utils.setup') as mock_setup:
        try:
            main(['-i'])
        except SystemExit as e:
            assert e.code == 0
        mock_setup.assert_called_once_with(None)

def test_kill():
    with patch('grongier.pex._director._Director.shutdown_production') as mock_shutdown:
        try:
            main(['-k'])
        except SystemExit as e:
            assert e.code == 0
        mock_shutdown.assert_called_once()

def test_restart():
    with patch('grongier.pex._director._Director.restart_production') as mock_restart:
        try:
            main(['-r'])
        except SystemExit as e:
            assert e.code == 0
        mock_restart.assert_called_once()

def test_migrate_relative():
    with patch('grongier.pex._utils._Utils.migrate') as mock_migrate:
        try:
            main(['-m', 'settings.json'])
        except SystemExit as e:
            assert e.code == 0
        mock_migrate.assert_called_once_with(os.path.join(os.getcwd(), 'settings.json'))

def test_migrate_absolute():
    with patch('grongier.pex._utils._Utils.migrate') as mock_migrate:
        try:
            main(['-m', '/tmp/settings.json'])
        except SystemExit as e:
            assert e.code == 0
        mock_migrate.assert_called_once_with('/tmp/settings.json')

def test_stop():
    with patch('grongier.pex._director._Director.stop_production') as mock_stop:
        with patch('sys.stdout', new=StringIO()) as fake_out:
            try:
                main(['-S'])
            except SystemExit as e:
                assert e.code == 0
            mock_stop.assert_called_once()
            assert fake_out.getvalue().strip() == 'Production UnitTest.Production stopped'

def test_test():
    with patch('grongier.pex._director._Director.test_component') as mock_test:
        try:
            main(['-t', 'my_test', '-C', 'MyClass', '-B', 'my_body'])
        except SystemExit as e:
            assert e.code == 0
        mock_test.assert_called_once_with('my_test', classname='MyClass', body='my_body')

def test_test_japanese():
    with patch('grongier.pex._director._Director.test_component') as mock_test:
        try:
            main(['-t', 'my_test', '-C', 'MyClass', '-B', 'あいうえお'])
        except SystemExit as e:
            assert e.code == 0
        mock_test.assert_called_once_with('my_test', classname='MyClass', body='あいうえお')

