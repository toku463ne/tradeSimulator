import unittest
import __init__
from ticker.peaks import Peaks
from datetime import datetime
import pandas as pd
from db.postgresql import PostgreSqlDB
from consts import *

class TestPeakTicker(unittest.TestCase):
    def test_ticker(self):
        st = datetime(year=2021, month=11, day=1).timestamp()
        ed = datetime(year=2021, month=12, day=1).timestamp()

        conf = {
            "codename": "^N225",
            "granularity": "D",
            "startep": st,
            "endep": ed,
            "use_master": False
        }

        db = PostgreSqlDB()
        db.execSql("truncate table peaks_d_10;")
        db.execSql("truncate table peaks_ctrl;")

        t = Peaks(conf)
        self.assertTrue(t.tick())
        df = t.data

        self.assertEqual(df.dt[0].year, 2020)
        self.assertEqual(df.dt[0].month, 12)
        self.assertEqual(df.dt[0].day, 7)
        self.assertEqual(len(df), 18)

        self.assertEqual(df.dt[17].year, 2021)
        self.assertEqual(df.dt[17].month, 10)
        self.assertEqual(df.dt[17].day, 6)


        sql = "select * from peaks_ctrl where codename = '^N225';"
        (codename, tablename, startep, endep, startdt, enddt) = db.select1rec(sql)
        self.assertEqual(tablename, "peaks_D_10") 
        self.assertEqual(startdt.year, 2020) 
        self.assertEqual(startdt.month, 11) 
        self.assertEqual(startdt.day, 1) 
        self.assertEqual(enddt.year, 2021) 
        self.assertEqual(enddt.month, 11) 
        self.assertEqual(enddt.day, 1) 


if __name__ == "__main__":
    unittest.main()
