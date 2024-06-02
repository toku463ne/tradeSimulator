import __init__
import unittest
from datetime import datetime

from data_getter import getDataGetter
import lib.priceaction as pa
import lib

class TestPriceaction(unittest.TestCase):
    def _checkTrendRate(self, codename, startdt, enddt, expected_rate, expected_has_trend):
        dg = getDataGetter(codename, "D")
        (eps, dt, ol, hl, ll, cl, vl) = dg.getPrices(lib.dt2epoch(startdt), lib.dt2epoch(enddt))
        r, has_trend = pa.checkTrendRate(hl[-5:], ll[-5:], cl[-5:])
        self.assertEqual(int(r*10), expected_rate)
        self.assertEqual(has_trend, expected_has_trend)


    def test_checkTrendRate(self):
        self._checkTrendRate("4751.T", datetime(2020,10,25), datetime(2020,11,2), -2, True) # 4751.T_20201102.png
        self._checkTrendRate("1435.T", datetime(2018,2,25), datetime(2018,3,5), -9, True)
        self._checkTrendRate("1435.T", datetime(2018,3,25), datetime(2018,4,3), 8, True)
        self._checkTrendRate("1435.T", datetime(2018,4,10), datetime(2018,4,17), 4, False)
        
        


    def _checkLastCandle(self, codename, startdt, enddt,
                         expected_len_std, expected_hara_rate):
        dg = getDataGetter(codename, "D")
        (eps, dt, ol, hl, ll, cl, vl) = dg.getPrices(lib.dt2epoch(startdt), lib.dt2epoch(enddt))
        res = pa.checkLastCandle(ol[-5:], hl[-5:], ll[-5:], cl[-5:])
        self.assertEqual(int(res["len_std"]*10), expected_len_std)
        self.assertEqual(int(res["hara_rate"]*10), expected_hara_rate)
        

    def test_checkLastCandle(self):
        self._checkLastCandle("3382.T", datetime(2022,9,25), datetime(2022,10,3),19,-7)
        

if __name__ == "__main__":
    unittest.main()
