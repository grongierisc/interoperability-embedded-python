
import unittest
from unittest.mock import patch

from grongier.pex import _utils

class FilenameToModuleTest(unittest.TestCase):

    def test_singlefile(self):
        file = 'bo.py'
        result = _utils.filename_to_module(file)
        expect = 'bo'
        
        self.assertEqual(result, expect)
    
    def test_filenameWithPath(self):
        file = 'interop/bo.py'
        result = _utils.filename_to_module(file)
        expect = 'interop.bo'
        
        self.assertEqual(result, expect)

    def test_filenameWithoutExtension(self):
        file = 'bo'
        result = _utils.filename_to_module(file)
        expect = 'bo'
        
        self.assertEqual(result, expect)

class Register(unittest.TestCase):

    def test_register_component(self):
        module = 'bo'
        classname = 'EmailOperation'
        path = '/irisdev/app/src/python/grongier/tests/registerFiles/'
        overwrite = 1
        iris_classname = 'Test.EmailOperation'
        result = _utils.register_component(module, classname, path, overwrite, iris_classname)
        expect = 1
        
        self.assertEqual(result, expect)

    def test_register_folder(self):
        path = '/irisdev/app/src/python/grongier/tests/registerFiles/'
        overwrite = 1
        iris_classname = 'Path'
        result = _utils.register_folder(path, overwrite, iris_classname)
        expect = 1
        
        self.assertIsNone(result)

    def test_register_file(self):
        filename = 'bo.py'
        path = '/irisdev/app/src/python/grongier/tests/registerFiles/'
        overwrite = 1
        iris_classname = 'File'
        result = _utils.register_file(filename, path, overwrite, iris_classname)
        expect = 1
        
        self.assertIsNone(result)

    def test_register_package(self):
        package = 'registerFiles'
        path = '/irisdev/app/src/python/grongier/tests/'
        overwrite = 1
        iris_classname = 'Package'
        result = _utils.register_package(package, path, overwrite, iris_classname)
        expect = 1
        
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()