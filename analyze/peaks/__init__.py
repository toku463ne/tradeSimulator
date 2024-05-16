import sys, os, logging
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from datetime import datetime


import env
import lib
import lib.indicators as ind

import data_getter
from db.postgresql import PostgreSqlDB
import lib.naming as naming


def insertData(start, end, granularity, codes=[], size=10, is_test=False):
    if len(start) == 10:
        start = start + "T00:00:00"
        end = end + "T00:00:00"
    startep = lib.str2epoch(start)
    endep = lib.str2epoch(end)

    db = PostgreSqlDB()    
    if len(codes) == 0:
        sql = "select distinct codename from codes;"
        cur = db.execSql(sql)
        for (code,) in cur:
            codes.append(code)

    tableName = naming.peakTable(granularity, size)
    if not db.tableExists(tableName):
        db.createTable(tableName, "peaks")
    if not db.tableExists("peaks_ctrl"):
        db.createTable("peaks_ctrl")


    for instrument in codes:
        cnt = db.countTable("peaks_ctrl", [
            "codename = '%s'" % instrument,
            "tablename = '%s'" % tableName
        ])
        do_update = False
        if cnt > 0:
            sql = """select "start", "end" from peaks_ctrl
where codename = '%s' and tablename = '%s';""" % (instrument, tableName)
            (start_db, end_db) = db.select1rec(sql)
            if start_db > start:
                start_db = start
                do_update = True
            if end_db < end:
                end_db = end
                do_update = True
        

        if cnt > 0:
            sql = """update peaks_ctrl 
set "start" = '%s' "end" = '%s'
""" % (start_db, end_db)
        else:
            sql = """insert into 
    peaks_ctrl("codename", "tablename", "start", "end")
    values ('%s', '%s', '%s', '%s')
    ;""" % (instrument, tableName, start, end)
            
            db.execSql(sql)
        
        logging.info("Getting %s.." % instrument)
        dg = data_getter.getDataGetter(instrument, granularity, is_dgtest=is_test)
        (eps, dt, _, h, l, _, _) = dg.getPrices(startep, endep)
        peaks = ind.peaks(eps, dt, h, l, size)
        v_sql = ""

        

        for peak in peaks:
            if v_sql != "":
                v_sql += ","
            v_sql += "('%s', %d, %d, '%s', %f)" % (
                instrument, peak["ep"], peak["side"], peak["dt"], peak["price"]
            )

        if v_sql == "":
            continue
        
        sql = """insert into 
%s(codename, ep, side, DT, price) 
values %s ON CONFLICT (codename, ep, side) DO NOTHING;""" % (tableName, v_sql)
        
        db.execSql(sql)

        sql = """insert into 
peaks_ctrl("codename", "tablename", "start", "end")
values ('%s', '%s', '%s', '%s')
ON CONFLICT (codename, tablename) DO update set "start" = '%s', "end" = '%s'
;""" % (instrument, tableName, start, end, start, end)
        
        db.execSql(sql)


if __name__ == "__main__":
    env.loadConf("default.yaml")
    
    st = lib.dt2str(datetime(year=2016, month=4, day=1))
    ed = lib.dt2str(datetime(year=2024, month=4, day=1))
    
    insertData(st, ed, "D")
