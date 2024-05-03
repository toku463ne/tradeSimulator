import __init__

import unittest
import lib

import db.mysql as mysql
from backtest.accumulationStrategy import run_day_on_month

class TestAccBacktest(unittest.TestCase):
    def testCase1(self):
        codename = "^GSPC" #SP500
        startstr = "2022-01-01T00:00:00"
        endstr = "2024-01-01T00:00:00"
        orderstopstr = endstr

        report = run_day_on_month("test_acc_sp500_day01", codename, "D", startstr, endstr, orderstopstr, day=1)


        self.assertEqual(len(report),12)
        db = mysql.MySqlDB()
        self.assertEqual(db.countTable("trade_history", ["trade_name = 'test_accumulation'"]), 14)
        
        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()