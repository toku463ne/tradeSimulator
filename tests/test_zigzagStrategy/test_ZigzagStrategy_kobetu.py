import unittest
from datetime import datetime

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

    def _run(self, trade_name, codename, st, ed, 
            expected_cnt, expected_side, expected_result, expected_open_datetime):
        granularity = "D"
        args = {"codename": "^N225", 
        "granularity": granularity, 
        "codenames": [codename],
        "analize_mode": True,
        "use_master": True,
        "exclude_codes": ["^MSFT"],
        "n_targets": 10}
        strategy = ZigzagStrategy(args)
        ticker = TimeTicker(granularity, st, ed)
        executor = Executor()
        portforio = Portoforio(trade_name, 10000000, 0)
        tm = TradeManager("zigzag strategy", ticker, strategy, executor, portforio)
        tm.run(endep=ed, orderstopep=ed)
        
        db = PostgreSqlDB()
        cnt = 0
        for (side, result, open_datetime) in db.execSql("""SELECT side, result, open_datetime 
FROM trades
WHERE 
trade_name = '%s' AND
codename = '%s'
;""" % (trade_name, codename)):
            self.assertEqual(side, expected_side)
            self.assertEqual(result, expected_result)
            self.assertEqual(open_datetime, expected_open_datetime)
            cnt += 1

        self.assertEqual(cnt, expected_cnt)

    '''
    def test_3962T_20220721(self):
        st = lib.str2epoch("2022-07-20T00:00:00")
        ed = lib.str2epoch("2022-08-05T00:00:00")
        self._run("zz_kobetsu_3962.T_2022-07-27", "3962.T", st, ed, 1, SIDE_BUY, "lose", datetime(2022, 7, 28))
    '''

    '''  
    # No trade because trend is strange
    def test_6869T_20191125(self):
        st = lib.str2epoch("2019-11-20T00:00:00")
        ed = lib.str2epoch("2019-12-05T00:00:00")
        self._run("zz_kobetsu_6869.T_2019-11-26", "6869.T", st, ed, 0, 0, "", None)
    '''
         
    '''  
    # no trade because the close price is far from base line
    def test_1435T_20180418(self):
        st = lib.str2epoch("2018-04-10T00:00:00")
        ed = lib.str2epoch("2018-05-01T00:00:00")
        self._run("zz_kobetsu_1435.T_2018-04-18", "1435.T", st, ed, 0, 0, "", None)
    '''  
        
    '''  
    # no trade because order price is not within next candle
    def test_8233T_20210621(self):
        st = lib.str2epoch("2021-06-10T00:00:00")
        ed = lib.str2epoch("2021-07-01T00:00:00")
        self._run("zz_kobetsu_8233.T_2021-06-21", "8233.T", st, ed, 0, 0, "", None)
    '''  
        
    '''
    # no trade because order price is not within next candle
    def test_3382T_20221004(self):
        st = lib.str2epoch("2022-10-01T00:00:00")
        ed = lib.str2epoch("2022-10-10T00:00:00")
        self._run("zz_kobetsu_3382.T_2022-10-04", "3382.T", st, ed, 0, 0, "", None)    
    '''
    
    '''
    # trade at 2019/5/9
    # no trade at 2019/5/14 because order price is not within next candle
    def test_1812T_20190515(self):
        st = lib.str2epoch("2019-05-05T00:00:00")
        ed = lib.str2epoch("2019-05-16T00:00:00")
        self._run("zz_kobetsu_1812.T_2019-05-15", "1812.T", st, ed, 1, SIDE_BUY, "win", datetime(2019, 5, 10))
    '''

    '''
    # base line 4157. is a peak #6976_20221122.png
    def test_6976T_20190515(self):
        st = lib.str2epoch("2022-11-15T00:00:00")
        ed = lib.str2epoch("2022-12-03T00:00:00")
        self._run("zz_kobetsu_6976.T_2022-11-22", "6976.T", st, ed, 1, SIDE_BUY, "win", datetime(2022, 11, 30))
    '''


    def test_4185T_20190302(self):
        st = lib.str2epoch("2019-02-25T00:00:00")
        ed = lib.str2epoch("2019-03-10T00:00:00")
        self._run("zz_kobetsu_4185.T_2019-03-02", "4185.T", st, ed, 1, SIDE_BUY, "lose", datetime(2019, 3, 2))
    


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()