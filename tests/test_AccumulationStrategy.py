import __init__

import unittest
from strategy.AccumulationStrategy import AccumulationStrategy
import lib
import lib.tradelib as tradelib
from time_ticker import TimeTicker
from executor import Executor
from trade_manager import TradeManager
from portforio import Portoforio
import db.mysql as mysql

class TestAccumulationStrategy(unittest.TestCase):

    def _run(self, st, ed, os, acc_timing):
        codename = "^N225"
        granularity = "D"
        args = {"codename": codename, 
        "granularity": granularity, 
        "acc_timing": acc_timing}
        strategy = AccumulationStrategy(args)
        ticker = TimeTicker(granularity, st, ed)
        executor = Executor()
        portforio = Portoforio("test_accumulation", 1000000, 0)
        tm = TradeManager("accumulation strategy", ticker, strategy, executor, portforio)
        report = tm.run(endep=ed, orderstopep=os)
        #import json
        #print(json.dumps(tm.portforio.history, indent=4))

        return report


    def testCase1(self):
        st = lib.str2epoch("2021-10-01T00:00:00")
        ed = lib.str2epoch("2022-12-01T00:00:00")
        os = lib.str2epoch("2022-11-20T00:00:00")
        report = self._run(st, ed, os, {
            "name": "day_on_month",
            "day": 1
        })
        self.assertEqual(len(report),12)
        db = mysql.MySqlDB()
        self.assertEqual(db.countTable("trade_history", ["trade_name = 'test_accumulation'"]), 14)
        
        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()