import unittest
from datetime import datetime
from datetime import timedelta

import __init__
from strategy.ZigzagStrategy import ZigzagStrategy
import lib
from time_ticker import TimeTicker
from executor import Executor
from trade_manager import TradeManager
from portforio import Portoforio
from db.postgresql import PostgreSqlDB
from consts import *

class TestPeakStrategy(unittest.TestCase):

    def _run(self, trade_name, codename, order_date, st, ed, 
            expected_cnt, expected_side=SIDE_BUY, expected_result="", expected_open_datetime=None):
        granularity = "D"
        args = {"codename": "^N225", 
        "granularity": granularity, 
        "codenames": [codename],
        "analize_mode": True,
        "trade_name": trade_name,
        "use_master": True,
        "exclude_codes": ["^MSFT"],
        "debug_date": order_date,
        "n_targets": 10}
        strategy = ZigzagStrategy(args)
        ticker = TimeTicker(granularity, st, ed)
        executor = Executor()
        portforio = Portoforio(trade_name, 10000000, 0)
        tm = TradeManager("zigzag strategy", ticker, strategy, executor, portforio)
        tm.run(endep=ed, orderstopep=ed)
        
        db = PostgreSqlDB()
        res = db.execSql("""SELECT side, result, open_datetime 
FROM trades
WHERE 
trade_name = '%s' AND
codename = '%s'
;""" % (trade_name, codename))
        
        if res is None:
            self.assertEqual(expected_cnt, 0)
            return

        cnt = 0
        for (side, result, open_datetime) in res:
            self.assertEqual(side, expected_side)
            self.assertEqual(result, expected_result)
            self.assertEqual(open_datetime, expected_open_datetime)
            cnt += 1

        self.assertEqual(cnt, expected_cnt)

    def _checkStrtgParams(self, trade_name, params):
        db = PostgreSqlDB()
        for (key, expected_val) in params.items():
            (val,) = db.select1rec("SELECT %s FROM zz_strtg_params WHERE order_id LIKE '%%%s';" % (key, trade_name))
            self.assertEqual(val, expected_val)


    
    def test_1306T(self):
        codename = "6479.T"
        order_date = datetime(2018,8,14)
        open_date = datetime(2018,8,15)
        st = lib.dt2epoch(order_date - timedelta(days=5))
        ed = lib.dt2epoch(order_date + timedelta(days=10))
        self._run("zz_kobetsu_%s_%s" % (codename, lib.dt2str(order_date, "%Y-%m-%d")), 
                  codename, order_date, st, ed, 1, SIDE_BUY, "win", open_date)
    

    


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()