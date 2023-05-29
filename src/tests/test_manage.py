import pytest
import grongier.pex._manager as _manager

def test_help():
    # test help
    try:
        _manager.main(['-h'])
    except SystemExit as e:
        assert e.code == 0

def test_default_with_name():
    # test default
    try:
        _manager.main(['-d', 'UnitTest.Production'])
    except SystemExit as e:
        assert e.code == 0

def test_default_without_name():
    # test default
    try:
        _manager.main(['-d'])
    except SystemExit as e:
        assert e.code == 0

