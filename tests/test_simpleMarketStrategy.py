import __init__

import unittest
from strategy.SimpleMarketStrategy import SimpleMarketStrategy
import lib
from time_ticker import TimeTicker
from executor import Executor
from trade_manager import TradeManager
from portforio import Portoforio

class TestSimpleMarketStrategy(unittest.TestCase):

    def _run(self, st, ed, os, profit):
        codename = "^N225"
        granularity = "D"
        args = {"codename": codename, 
        "granularity": granularity, 
        "profit": profit}
        strategy = SimpleMarketStrategy(args)
        ticker = TimeTicker(granularity, st, ed)
        executor = Executor()
        portforio = Portoforio("test_simplemarket", 1000000, 1000000)
        tm = TradeManager("market strategy", ticker, strategy, executor, portforio)
        report = tm.run(endep=ed, orderstopep=os)

        return report


    def testCase1(self):
        st = lib.str2epoch("2021-10-01T00:00:00")
        ed = lib.str2epoch("2021-12-01T00:00:00")
        os = lib.str2epoch("2021-11-20T00:00:00")
        report = self._run(st, ed, os, 500)
        self.assertEqual(len(report),12)
        
        st = lib.str2epoch("2021-06-01T00:00:00")
        ed = lib.str2epoch("2021-12-01T00:00:00")
        os = lib.str2epoch("2021-11-20T00:00:00")
        report = self._run(st, ed, os, 1000)
        self.assertEqual(report["trade_count"], 6)
        self.assertEqual(int(report["buy_offline"]), 920)
        
        report = self._run(st, ed, os, 700)
        self.assertEqual(report["trade_count"], 13)
        self.assertEqual(int(report["buy_offline"]), 442)
        
        report = self._run(st, ed, os, 500)
        self.assertEqual(report["trade_count"], 18)
        self.assertEqual(int(report["sell_offline"]), 423)
        
        st = lib.str2epoch("2021-06-01T00:00:00")
        ed = lib.str2epoch("2021-09-01T00:00:00")
        os = lib.str2epoch("2021-08-20T00:00:00")
        report = self._run(st, ed, os, 1000)
        self.assertEqual(report["trade_count"], 4)
        self.assertEqual(int(report["sell_offline"]), 1987)
        self.assertEqual(int(report["buy_offline"]), -27241)
        

        #print(report)
        #import json
        #print(json.dumps(tm.portforio.history, indent=4))

        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()