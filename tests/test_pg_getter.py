import __init__
import unittest
import data_getter.yfinance_getter as yfinance_getter
import data_getter.pg_getter as pg_getter
import db.postgresql as pgdb
from datetime import datetime

import pandas as pd

import lib

class TestYfPgGetter(unittest.TestCase):
    def test_yfmygetter(self):
        pg = pgdb.PostgreSqlDB()
        if pg.tableExists("ohlcv_D"):
            pg.execSql("delete from ohlcv_D where codename = 'MSFT';")
            pg.execSql("delete from ohlcv_ctrl where tablename = 'ohlcv_D' and codename = 'MSFT';")
        
        yg = yfinance_getter.YFinanceGetter("MSFT", "D")
        pgg = pg_getter.PgGetter(yg, is_dgtest=True)
        ctrl_sql = "select startep,endep from ohlcv_ctrl where tablename = 'ohlcv_D' and codename = 'MSFT';"

        
        st = datetime(year=2021, month=11, day=1, hour=9).timestamp()
        ed = datetime(year=2021, month=12, day=1, hour=9).timestamp()
        (ep, dt, o, h, l, c, v) = pgg.getPrices(st, ed)
        self.assertEqual(pd.to_datetime(dt[0]).day, 1)
        self.assertEqual(pd.to_datetime(dt[-2]).day, 30)
        self.assertEqual(22, len(ep))
        self.assertEqual(22, pg.countTable("ohlcv_D", ["codename = 'MSFT'"]))

        (ctrl_start, ctrl_end) = pgg.getCtrlInfo()
        self.assertEqual(ctrl_start, st)
        self.assertEqual(ctrl_end, ed)
        (db_ctrl_start, db_ctrl_end) = pg.select1rec(ctrl_sql)
        self.assertEqual(ctrl_start, db_ctrl_start)
        self.assertEqual(ctrl_end, db_ctrl_end)
        
        

        st = datetime(year=2021, month=11, day=15, hour=9).timestamp()
        ed = datetime(year=2021, month=12, day=14, hour=9).timestamp()
        (ep, dt, o, h, l, c, v) = pgg.getPrices(st, ed)
        self.assertEqual(21, len(ep))
        self.assertEqual(pd.to_datetime(dt[0]).day, 15)
        self.assertEqual(pd.to_datetime(dt[-1]).day, 14)
        self.assertEqual(31, pg.countTable("ohlcv_D", ["codename = 'MSFT'"]))

        (ctrl_start, ctrl_end) = pgg.getCtrlInfo()
        self.assertEqual(ctrl_start, datetime(year=2021, month=11, day=1, hour=9).timestamp())
        self.assertEqual(ctrl_end, datetime(year=2021, month=12, day=14, hour=9).timestamp())
        (db_ctrl_start, db_ctrl_end) = pg.select1rec(ctrl_sql)
        self.assertEqual(ctrl_start, db_ctrl_start)
        self.assertEqual(ctrl_end, db_ctrl_end)
        
        
        st = datetime(year=2021, month=10, day=11, hour=9).timestamp()
        ed = datetime(year=2021, month=10, day=15, hour=9).timestamp()
        (ep, dt, o, h, l, c, v) = pgg.getPrices(st, ed)
        self.assertEqual(pd.to_datetime(dt[0]).day, 11)
        self.assertEqual(pd.to_datetime(dt[-1]).day, 15)
        self.assertEqual(46, pg.countTable("ohlcv_D", ["codename = 'MSFT'"]))

        (ctrl_start, ctrl_end) = pgg.getCtrlInfo()
        self.assertEqual(ctrl_start, st)
        self.assertEqual(ctrl_end, datetime(year=2021, month=12, day=14, hour=9).timestamp())
        (db_ctrl_start, db_ctrl_end) = pg.select1rec(ctrl_sql)
        self.assertEqual(ctrl_start, db_ctrl_start)
        self.assertEqual(ctrl_end, db_ctrl_end)
       
        #print(p)

if __name__ == "__main__":
    unittest.main()
