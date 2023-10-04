import grongier.pex._cli as _cli

def test_help():
    # test help
    try:
        _cli.main(['-h'])
    except SystemExit as e:
        assert e.code == 0

def test_default_with_name():
    # test default
    try:
        _cli.main(['-d', 'UnitTest.Production'])
    except SystemExit as e:
        assert e.code == 0
        # assert the output
        assert _cli._Director.get_default_production() == 'UnitTest.Production'

def test_default_without_name():
    # test default
    try:
        _cli.main(['-d'])
    except SystemExit as e:
        assert e.code == 0

def test_cli_namespace():
    try:
        _cli.main([])
    except SystemExit as e:
        assert e.code == 0

