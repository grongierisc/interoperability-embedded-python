import iris
import os
import sys

from grongier.pex._utils import _Utils

from unittest.mock import patch, MagicMock

def test_filename_to_module():
    # test filename_to_module
    file = 'bo.py'
    result = _Utils.filename_to_module(file)
    expect = 'bo'
    
    assert result == expect

def test_raise_on_error():
    # test raise_on_error
    try:
        sc = iris.system.Status.Error('test')
        _Utils.raise_on_error(sc)
    except RuntimeError as e:
        assert True

def test_setup():
    # test setup
    try:
        _Utils.setup()
    except RuntimeError as e:
        assert False

def test_register_component():
    module = 'bo'
    classname = 'EmailOperation'
    # get the path of the current file
    path = os.path.dirname(os.path.realpath(__file__))
    # join the registerFolder to the path
    path = os.path.join(path, 'registerFiles')
    overwrite = 1
    iris_classname = 'UnitTest.EmailOperation'
    result = _Utils.register_component(module, classname, path, overwrite, iris_classname)
    expect = 1

    assert result == expect

def test_register_folder():
    path = os.path.dirname(os.path.realpath(__file__))
    # join the registerFolder to the path
    path = os.path.join(path, 'registerFiles')
    overwrite = 1
    iris_classname = 'UnitTest.Path'
    result = _Utils.register_folder(path, overwrite, iris_classname)
    expect = None

    assert result == expect

def test_register_file():
    filename = 'bo.py'
    path = os.path.dirname(os.path.realpath(__file__))
    # join the registerFolder to the path
    path = os.path.join(path, 'registerFiles')
    filename = os.path.join(path, filename)
    overwrite = 1
    iris_classname = 'UnitTest.File'
    result = _Utils.register_file(filename, overwrite, iris_classname)
    expect = None

    assert result == expect

def test_register_package():
    package = 'registerFiles'
    path = os.path.dirname(os.path.realpath(__file__))
    overwrite = 1
    iris_classname = 'UnitTest.Package'
    result = _Utils.register_package(package, path, overwrite, iris_classname)
    expect = None

    assert result == expect

def test_set_classes_settings_by_classe():
    # set python path to the registerFiles folder
    path = os.path.dirname(os.path.realpath(__file__))
    # join the registerFolder to the path
    path = os.path.join(path, 'registerFiles')

    sys.path.append(path)

    from bo import EmailOperation
    CLASSES = { 'UnitTest.Package.EmailOperation': EmailOperation }
    _Utils.set_classes_settings(CLASSES)

def test_set_classes_settings_by_class_with_rootpath():
    # set python path to the registerFiles folder
    path = os.path.dirname(os.path.realpath(__file__))
    # join the registerFolder to the path
    path = os.path.join(path, 'registerFiles')

    sys.path.append(path)

    from bo import EmailOperation
    CLASSES = { 'UnitTest.Package.EmailOperation': EmailOperation }
    _Utils.set_classes_settings(CLASSES,path)

def test_set_classes_settings_by_module():
    # this test aim to register a module
    # set python path to the registerFiles folder
    path = os.path.dirname(os.path.realpath(__file__))
    # join the registerFolder to the path
    path = os.path.join(path, 'registerFiles')

    sys.path.append(path)
    import bo
    CLASSES = { 'UnitTest.Module': bo }
    _Utils.set_classes_settings(CLASSES)

def test_set_classes_settings_by_module_with_rootpath():
    # this test aim to register a module
    # set python path to the registerFiles folder
    path = os.path.dirname(os.path.realpath(__file__))
    # join the registerFolder to the path
    path = os.path.join(path, 'registerFiles')

    sys.path.append(path)
    import bo
    CLASSES = { 'UnitTest.Module': bo }
    _Utils.set_classes_settings(CLASSES,path)

def test_set_classes_settings_by_file():
    # set python path to the registerFiles folder
    path = os.path.dirname(os.path.realpath(__file__))
    # join the registerFolder to the path
    path = os.path.join(path, 'registerFiles')
    CLASSES = { 'UnitTest.File': {
        'file': 'bo.py',
        'class': 'EmailOperation',
        'module': 'bo',
        'path': path
    } }
    _Utils.set_classes_settings(CLASSES)

def test_set_classes_settings_by_folder():
    # set python path to the registerFiles folder
    path = os.path.dirname(os.path.realpath(__file__))
    # join the registerFolder to the path
    path = os.path.join(path, 'registerFiles')
    CLASSES = { 'UnitTest.Path': {
        'path': path
    } }
    _Utils.set_classes_settings(CLASSES)

def test_set_classes_settings_by_package():
    # set python path to the registerFiles folder
    path = os.path.dirname(os.path.realpath(__file__))
    CLASSES = { 'UnitTest.Package': {
        'package': 'registerFiles',
        'path': path
    } }
    _Utils.set_classes_settings(CLASSES)

def test_set_classes_settings_by_package_and_module():
    # set python path to the registerFiles folder
    path = os.path.dirname(os.path.realpath(__file__))
    # join the registerFolder to the path
    path = os.path.join(path, 'registerFiles')
    CLASSES = { 'UnitTest.Package.EmailOperation': {
        'path': path,
        'module': 'bo',
        'class': 'EmailOperation'
    } }
    _Utils.set_classes_settings(CLASSES)

def test_set_productions_settings():
    PRODUCTIONS = [
        {
            'UnitTest.Production': {
                "@TestingEnabled": "true",
                "Description": "",
                "ActorPoolSize": "2",
                "Item": [
                    {
                        "@Name": "Python.FileOperation",
                        "@ClassName": "Python.FileOperation",
                        "@Enabled": "true",
                        "@Foreground": "false",
                        "@LogTraceEvents": "true",
                        "Setting": {
                            "@Target": "Host",
                            "@Name": "%settings",
                            "#text": "path=/tmp"
                        }
                    }
                ]
            }
        } 
    ]
    _Utils.set_productions_settings(PRODUCTIONS)

def test_get_productions_settings():
    PRODUCTIONS = [
        {
            'UnitTest.Production': {
                "@TestingEnabled": "true",
                "Description": "",
                "ActorPoolSize": "2",
                "Item": [
                    {
                        "@Name": "Python.FileOperation",
                        "@ClassName": "Python.FileOperation",
                        "@Enabled": "true",
                        "@Foreground": "false",
                        "@LogTraceEvents": "true",
                        "Setting": {
                            "@Target": "Host",
                            "@Name": "%settings",
                            "#text": "path=/tmp"
                        }
                    },
                    {
                        "@Name": "Python.EmailOperation",
                        "@ClassName": "UnitTest.Package.EmailOperation"
                    }
                ]
            }
        } 
    ]
    _Utils.set_productions_settings(PRODUCTIONS)
    result = _Utils.export_production('UnitTest.Production')
    expect = PRODUCTIONS[0]

    assert result == expect


def test_migrate_only_classes():
    # Arrange
    mock_settings = MagicMock()
    mock_settings.CLASSES = {'MyClass': MagicMock()}
    mock_settings.__file__ = '/path/to/settings/settings.py'
    # set magic mock as an object
    mock_settings.__class__ = type
    # add mock_settings to sys.modules and __file__ to mock_settings
    with patch.dict('sys.modules', {'settings': mock_settings}):
        # Act
        _Utils.migrate('/path/to/settings/settings.py')
        # Assert
        assert True # if no exception is raised, the test is ok