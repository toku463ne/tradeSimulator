import unittest
import __init__
import lib.indicators as ind

class TestSma(unittest.TestCase):
    def test_smd(self):
        a = [1,2,3,4,5,6,7,8,9,10]
        smd, i = ind.smd(a, 5)
        self.assertEqual(len(smd), 5)
        self.assertEqual(i, 4)




if __name__ == "__main__":
    unittest.main()
