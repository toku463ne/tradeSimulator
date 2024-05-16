import __init__
import unittest
from datetime import datetime
import analyze.peaks as peaks
import db.postgresql as pg
import lib

class TestPeaks(unittest.TestCase):
    def test_peaks(self):
        db = pg.PostgreSqlDB()
        db.truncateTable("peaks_d_10")

        codes = ["7203.T"]
        st = lib.dt2str(datetime(year=2023, month=8, day=1, hour=9))
        ed = lib.dt2str(datetime(year=2024, month=2, day=1, hour=9))

        peaks.prepare(st, ed, "D", codes, is_test=True)

        self.assertEqual(db.countTable("peaks_d_10", ["codename = '7203.T'"]), 7)

        #cur = db.execSql("select * from peaks_D_20;")




if __name__ == "__main__":
    unittest.main()

