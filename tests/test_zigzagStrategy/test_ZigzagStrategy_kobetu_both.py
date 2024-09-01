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

ref_trade_name = "zzstrat_top3000vol2"

class TestPeakStrategy(unittest.TestCase):

    def _run(self, trade_name, codename, order_date, 
            expected_cnt, expected_side=SIDE_BUY, expected_result="", expected_open_datetime=None):
        st = lib.dt2epoch(order_date - timedelta(days=5))
        ed = lib.dt2epoch(order_date + timedelta(days=20))
        granularity = "D"
        args = {"codename": "^N225", 
        "granularity": granularity, 
        "codenames": [codename],
        "analize_mode": True,
        "trade_name": trade_name,
        "ref_trade_name": ref_trade_name,
        "use_master": True,
        "exclude_codes": ["^MSFT"],
        "debug_date": order_date,
        "n_targets": 10}
        strategy = ZigzagStrategy(args)
        ticker = TimeTicker(granularity, st, ed)
        executor = Executor()
        portforio = Portoforio(trade_name, 10000000, 10000000)
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


    """
    def test_6479T(self):
        codename = "6479.T"
        order_date = datetime(2018,3,28)
        open_date = datetime(2018,3,29)
        
        self._run("zz_kobetsu_%s_%s" % (codename, lib.dt2str(order_date, "%Y-%m-%d")), 
                  codename, order_date, 1, SIDE_SELL, "win", open_date)
    
        order_date = datetime(2018,4,5)
        open_date = datetime(2018,4,6)
        self._run("zz_kobetsu_%s_%s" % (codename, lib.dt2str(order_date, "%Y-%m-%d")), 
                  codename, order_date, 1, SIDE_BUY, "win", open_date)
    """
                  

    def test_4042T(self):
        codename = "4042.T"
        order_date = datetime(2017,4,26)
        open_date = datetime(2017,4,27)
        #self._run("zz_kobetsu_%s_%s" % (codename, lib.dt2str(order_date, "%Y-%m-%d")), 
        #          codename, order_date, 1, SIDE_BUY, "win", open_date)
    
        order_date = datetime(2017,5,23)
        open_date = datetime(2017,5,31)
        #self._run("zz_kobetsu_%s_%s" % (codename, lib.dt2str(order_date, "%Y-%m-%d")), 
        #          codename, order_date, 1, SIDE_BUY, "win", open_date)
    
        order_date = datetime(2018,7,26)
        open_date = datetime(2018,7,27)
        #self._run("zz_kobetsu_%s_%s" % (codename, lib.dt2str(order_date, "%Y-%m-%d")), 
        #          codename, order_date, 0, 0, "", None)

        order_date = datetime(2018,7,27)
        open_date = datetime(2018,7,28)
        self._run("zz_kobetsu_%s_%s" % (codename, lib.dt2str(order_date, "%Y-%m-%d")), 
                  codename, order_date, 0, 0, "", None)




if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()