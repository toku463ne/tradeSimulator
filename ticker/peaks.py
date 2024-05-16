import logging
import pandas as pd

from ticker import Ticker
import lib
import lib.indicators as libind
from db.postgresql import PostgreSqlDB
from db.pgdf import PgDf
import lib.naming as naming
import data_getter


class Peaks(Ticker):
    def __init__(self, config):
        super(Peaks, self).__init__(config)
        self.size = config.get("size", 10)
        self.period = config.get("period", 365)

        #self.initData()

    #def initData(self, ohlcv=[]):
    #    #super(Peaks, self).initData(ohlcv)
    #    pass
        

    #self, i, n=0
    def getData(self, i, n=0):        
        if n == 1 and i >= 0:
            endep = self.eps[i]
            startep = endep - self.unitsecs*self.period
        elif i >= 0:
            j = i-n+1
            endep = self.eps[i]
            startep = self.eps[j]
        else:
            return None


        granularity = self.granularity
        size = self.size
        codename = self.codename

        db = PostgreSqlDB()

        tableName = naming.peakTable(granularity, size)
        if not db.tableExists(tableName):
            db.createTable(tableName, "peaks")
        if not db.tableExists("peaks_ctrl"):
            db.createTable("peaks_ctrl")


        def getDf(startep, endep):
            sql = """SELECT codename, ep, side, dt, price FROM %s
WHERE ep >= %d and ep <= %d and codename = '%s'""" % (tableName, startep, endep, codename)
            return PgDf().read_sql(sql)
            


        ranges = []
        cnt = db.countTable("peaks_ctrl", [
            "codename = '%s'" % codename,
            "tablename = '%s'" % tableName
        ])
        do_update = False
        if cnt > 0:
            sql = """select "startep", "endep" from peaks_ctrl
where codename = '%s' and tablename = '%s';""" % (codename, tableName)
            (startep_db, endep_db) = db.select1rec(sql)
            if startep_db > startep:
                ranges.append((startep, startep_db))
                startep_db = startep
                do_update = True
            if endep_db < endep:
                ranges.append((endep_db, endep))
                endep_db = endep
                do_update = True
        else:
            do_update = True
            ranges.append((startep, endep))
            startep_db = startep
            endep_db = endep
        
        if do_update == False:
            return getDf(startep, endep)

        logging.info("Getting %s.." % codename)
        # calculate peaks and insert into peaks_ table
        for (rstartep, rendep) in ranges:
            dg = data_getter.getDataGetter(codename, granularity, is_dgtest=self.use_master)
            (eps, dt, _, h, l, _, _) = dg.getPrices(rstartep, rendep)
            peaks = libind.peaks(eps, dt, h, l, size)
            v_sql = ""
        

            for peak in peaks:
                if v_sql != "":
                    v_sql += ","
                v_sql += "('%s', %d, %d, '%s', %f)" % (
                    codename, peak["ep"], peak["side"], peak["dt"], peak["price"]
                )

            if v_sql == "":
                continue
            
            sql = """insert into 
    %s(codename, ep, side, DT, price) 
    values %s ON CONFLICT (codename, ep, side) DO NOTHING;""" % (tableName, v_sql)
        
            db.execSql(sql)

        
        sql = """insert into 
peaks_ctrl("codename", "tablename", "startdt", "enddt", "startep", "endep")
values ('%s', '%s', '%s', '%s', %d, %d)
ON CONFLICT (codename, tablename) DO update set "startdt" = '%s', "enddt" = '%s', "startep" = %d, "endep" = %d
;""" % (codename, tableName, 
        lib.epoch2dt(startep_db), lib.epoch2dt(endep_db), startep_db, endep_db,
        lib.epoch2dt(startep_db), lib.epoch2dt(endep_db), startep_db, endep_db)
        db.execSql(sql)
        
        return getDf(startep, endep)
    
