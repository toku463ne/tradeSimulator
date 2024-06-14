import __init__
import unittest

from strategy.ZigzagStrategy.randomforest import RandomForest
import lib

class TestPeakStrategy(unittest.TestCase):
    def test(self):
        rf = RandomForest(use_master=True)
        rf.feed("zzstrat_top1000vol", lib.str2epoch("2018-01-01T00:00:00"), lib.str2epoch("2019-01-01T00:00:00"))




if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()