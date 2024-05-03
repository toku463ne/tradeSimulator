import __init__
import unittest
import data_getter.yfinance_getter as yfinance_getter
import data_getter.pg_getter as pg_getter
import db.postgresql as pgdb
from datetime import datetime

import pandas as pd

class TestYfPgGetter(unittest.TestCase):
    def test_yfmygetter(self):
        yg = yfinance_getter.YFinanceGetter("MSFT", "D")
        pgg = pg_getter.PgGetter(yg, is_dgtest=True)
        pg = pgdb.PostgreSqlDB()

        if pg.tableExists("ohlcv_D"):
            pg.execSql("delete from ohlcv_D where codename = 'MSFT';")
        
        st = datetime(year=2021, month=11, day=1, hour=9).timestamp()
        ed = datetime(year=2021, month=12, day=1, hour=9).timestamp()
        (ep, dt, o, h, l, c, v) = pgg.getPrices(st, ed)
        self.assertEqual(pd.to_datetime(dt[0]).day, 1)
        self.assertEqual(pd.to_datetime(dt[-2]).day, 30)
        self.assertEqual(22, len(ep))
        self.assertEqual(35, pg.countTable("ohlcv_D"))
        
        st = datetime(year=2021, month=11, day=15, hour=9).timestamp()
        ed = datetime(year=2021, month=12, day=14, hour=9).timestamp()
        (ep, dt, o, h, l, c, v) = pgg.getPrices(st, ed)
        self.assertEqual(21, len(ep))
        self.assertEqual(pd.to_datetime(dt[0]).day, 15)
        self.assertEqual(pd.to_datetime(dt[-1]).day, 14)
        self.assertEqual(44, pg.countTable("ohlcv_D"))
        
        st = datetime(year=2021, month=10, day=11, hour=9).timestamp()
        ed = datetime(year=2021, month=10, day=15, hour=9).timestamp()
        (ep, dt, o, h, l, c, v) = pgg.getPrices(st, ed)
        self.assertEqual(pd.to_datetime(dt[0]).day, 11)
        self.assertEqual(pd.to_datetime(dt[-1]).day, 15)
        self.assertEqual(59, pg.countTable("ohlcv_D"))
        
       
        #print(p)

if __name__ == "__main__":
    unittest.main()
