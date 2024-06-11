import __init__
import unittest
import data_getter
from datetime import datetime
import lib

import pandas as pd

class TestYfMyGetter(unittest.TestCase):
    def test_data_getter(self):
        startstr = '2018-04-16T00:00:00'
        endstr = '2018-07-25T00:00:00'
        dg = data_getter.getDataGetter("1570.T", "D")
        (eps, dt, ol, hl, ll, cl, vl) = dg.getPrices(lib.str2epoch(startstr),lib.str2epoch(endstr))
        
        self.assertGreater(len(eps), 0)

        
        
        #print(p)

if __name__ == "__main__":
    unittest.main()
