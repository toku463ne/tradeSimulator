import __init__

import unittest
from strategy.ZigzagStrategy import ZigzagStrategy
import lib
from time_ticker import TimeTicker
from executor import Executor
from trade_manager import TradeManager
from portforio import Portoforio
from db.postgresql import PostgreSqlDB

class TestPeakStrategy(unittest.TestCase):

    def _run(self, st, ed, os):
        codename = "^N225"
        granularity = "D"
        args = {"codename": codename, 
        "granularity": granularity, 
        "codenames": ["7733.T"],
        "analize_mode": True,
        "use_master": True,
        "exclude_codes": ["^MSFT"],
        "n_targets": 10}
        strategy = ZigzagStrategy(args)
        ticker = TimeTicker(granularity, st, ed)
        executor = Executor()
        portforio = Portoforio("test_zigzag_3405", 10000000, 0)
        tm = TradeManager("zigzag strategy", ticker, strategy, executor, portforio)
        report = tm.run(endep=ed, orderstopep=os)
        #import json
        #print(json.dumps(tm.portforio.history, indent=4))

        return report


    def testCase1(self):
        st = lib.str2epoch("2018-01-01T00:00:00")
        ed = lib.str2epoch("2019-12-01T00:00:00")
        os = lib.str2epoch("2019-11-20T00:00:00")
        report = self._run(st, ed, os)
        #self.assertEqual(len(report),12)
        db = PostgreSqlDB()
        self.assertEqual(db.countTable("trades", ["trade_name = 'test_zigzag_7203'"]), 2)
        
        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()