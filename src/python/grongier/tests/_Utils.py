
import unittest

from grongier.pex import Utils

class FilenameToModuleTest(unittest.TestCase):

    def test_singlefile(self):
        file = 'bo.py'
        result = Utils.filename_to_module(file)
        expect = 'bo'
        
        self.assertEqual(result, expect)
    
    def test_filenameWithPath(self):
        file = 'interop/bo.py'
        result = Utils.filename_to_module(file)
        expect = 'interop.bo'
        
        self.assertEqual(result, expect)

    def test_filenameWithoutExtension(self):
        file = 'bo'
        result = Utils.filename_to_module(file)
        expect = 'bo'
        
        self.assertEqual(result, expect)

if __name__ == '__main__':
    unittest.main()