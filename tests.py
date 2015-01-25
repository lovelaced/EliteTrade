import ed
import unittest

class system_tests(unittest.TestCase):
    
    def setUp(self):
        self.system  = ed.system("Test0101", 0.1,0.2,0.3)
        self.system2 = ed.system("Test0102", 0.2,0.3,0.4)
    
    def test_constructor(self):
        #Make sure we construct the each system correctly.
        self.assertEqual(self.system.name, "Test0101")
        self.assertEqual(self.system.x, 0.1)
        self.assertEqual(self.system.y, 0.2)
        self.assertEqual(self.system.z, 0.3)

    def test_calc_distance(self):
        self.assertEqual(self.system.calc_distance(self.system2), 0.17320508075688776)

class systems_tests(unittest.TestCase):
    pass    

if __name__ == '__main__':
    unittest.main()
