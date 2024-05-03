import unittest
import __init__
from ticker.ichimoku import Ichimoku
from datetime import datetime
import pandas as pd
from consts import *
import lib

class TestIchimoku(unittest.TestCase):


    def test_ichimoku_ticker(self):
        st = lib.dt2epoch(datetime(year=2021, month=2, day=1))
        ed = lib.dt2epoch(datetime(year=2021, month=4, day=1))
        
        t = Ichimoku({"codename": "^N225", 
                 "granularity": "D", 
                 "startep": st, 
                 "endep": ed})
        
        res = t.tick()
        self.assertTrue(res)


        (ep, dt, p) = t.data
        self.assertEqual(pd.to_datetime(dt).day, 8)
        self.assertEqual(pd.to_datetime(dt).month, 11)
        self.assertTrue(ep > 0.0)
        self.assertTrue(p > 0.0)
        
        self.assertTrue(t.tick())
        (ep, dt, p) = t.data
        self.assertEqual(pd.to_datetime(dt).day, 9)
        self.assertEqual(pd.to_datetime(dt).month, 11)
        
        self.assertTrue(t.tick(ep + t.unitsecs*2))
        (ep, dt, p) = t.data
        self.assertEqual(pd.to_datetime(dt).day, 11)
        self.assertEqual(pd.to_datetime(dt).month, 11)
        
        self.assertTrue(t.tick(ep - t.unitsecs*6))
        (ep_err, dt, p) = t.data
        self.assertEqual(ep_err, 0)
        self.assertEqual(t.err, TICKER_NODATA)
        

        self.assertTrue(t.tick(ep + t.unitsecs*20))
        (ep, dt, p) = t.data
        self.assertEqual(pd.to_datetime(dt).day, 1)
        self.assertEqual(pd.to_datetime(dt).month, 12)
        
        self.assertFalse(t.tick())
        (ep, dt, p) = t.data
        self.assertEqual(ep, 0)
        self.assertEqual(t.err, TICKER_ERR_EOF)
        


if __name__ == "__main__":
    unittest.main()
