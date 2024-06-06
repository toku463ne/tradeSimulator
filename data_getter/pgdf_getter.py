from http.client import REQUEST_URI_TOO_LONG
import lib.sqlib as sqlib
import lib.naming as naming
import lib
import math

from data_getter import DataGetter
import db.pgdf as pgdf
import db.postgresql as pg


class PgDfGetter(DataGetter):
    def __init__(self, childDG, is_dgtest=False):
        is_master = True
        if is_dgtest: # always refer to data in the main database
            is_master = False

        super(PgDfGetter, self).__init__(childDG)
        self.childDG = childDG
        self.name = "pgdfgetter_%s_%s" % (self.codename, self.granularity)
        self.tablename = naming.ohlcvTable(self.granularity)
        self.ctrl_tablename = "ohlcv_ctrl"
        self.is_master = is_master
        self.df = pgdf.PgDf(is_master=is_master)
        self.db = pg.PostgreSqlDB(is_master=is_master)
        if self.db.tableExists(self.tablename) == False:
            self.db.createTable(self.tablename, "ohlcv")
        if self.db.tableExists(self.ctrl_tablename) == False:
            self.db.createTable(self.ctrl_tablename)

        self.ctrl_start = 0
        self.ctrl_end = 0

        self.loadCtrlTable()


    def loadCtrlTable(self):
        res = self.db.select1rec("SELECT startep, endep FROM %s WHERE tablename = '%s' and codename = '%s';" % (
            self.ctrl_tablename, self.tablename, self.codename))
        if res is not None:
            (startep, endep) = res
        else:
            (startep, endep) = (0, 0)
        self.ctrl_start = startep
        self.ctrl_end = endep

    def getCtrlInfo(self):
        return self.ctrl_start, self.ctrl_end

    def updateCtrlTable(self, startep, endep):
        startdt = lib.epoch2str(startep)
        enddt = lib.epoch2str(endep)
        self.db.execSql("""insert into 
%s(codename, tablename, startep, endep, startdt, enddt)
values('%s', '%s', %d, %d, '%s', '%s')
on conflict (tablename, codename) do update
set startep = %d, endep = %d, startdt = '%s', enddt = '%s'
""" % (
        self.ctrl_tablename,
        self.codename, self.tablename, startep, endep, startdt, enddt,
        startep, endep, startdt, enddt
)
        )
        self.ctrl_start = startep
        self.ctrl_end = endep


    def getMinMaxEpoch(self):
        if self.db.tableExists(self.tablename) == False:
            return (0, 0)
        (min, max) = self.db.select1rec("select min(EP), max(EP) from %s where codename = '%s';" % (self.tablename, self.codename))
        if min == None:
            min = 0
        if max == None:
            max = 0
        return (int(min), int(max))

    def getData(self, cols=[], condList=[]):
        condList.append("codename = '%s'" % self.codename)
        strWhere = sqlib.list2wheresql(condList)
        strCols = "*"
        if len(cols) > 0:
            strCols = ",".join(cols)
        sql = "select %s from %s %s order by EP;" % (strCols, self.tablename, strWhere)
        df = self.df.read_sql(sql)
        return df

    def upsertData(self, df):
        if len(df) == 0:
            return
    
        try:
            len(df.index)
        except:
            return

        #df.to_sql(self.tableName, 
        #    self.conn, if_exists='append', index=False)
        sql = "insert into %s(codename, EP, DT, O, H, L, C, V) values" % (self.tablename)
        vals = ""
        for i in range(len(df.index)):
            s = df.iloc[i]
            if math.isnan(s["O"]):
                continue
            dt = lib.dt2str(s["DT"], "%Y/%m/%d %H:%M:%S")
            rowv = "('%s', %i, '%s', %f, %f, %f, %f, %f)" % (self.codename, s["EP"], 
            dt, s["O"], s["H"], s["L"], s["C"], s["V"])
            
            if vals == "":
                vals = rowv
            else:
                vals += ",%s" % (rowv)
        sql += vals + " ON CONFLICT (codename, EP) DO NOTHING;"

        self.db.execSql(sql)


    def getPrices(self, startep, endep, waitDownload=True, buff_size=0):
        ctrl_start = self.ctrl_start
        ctrl_end = self.ctrl_end
        upd_startep = startep - self.unitsecs
        upd_endep = endep + self.unitsecs

        ctrl_updated = False
        if ctrl_start == 0 or ctrl_end == 0:
            (ctrl_start, ctrl_end) = self.getMinMaxEpoch()
            if ctrl_start > 0 and ctrl_end > 0:
                ctrl_updated = True

        
        if ctrl_start == 0 or ctrl_end == 0:
            self.upsertData(self._getPricesFromChild(upd_startep, upd_endep, waitDownload))
            if ctrl_start == 0:
                ctrl_start = startep
            if ctrl_end == 0:
                ctrl_end = endep
            ctrl_updated = True
            
        
        if startep < ctrl_start:
            self.upsertData(self._getPricesFromChild(upd_startep, ctrl_start + self.unitsecs, waitDownload))
            ctrl_start = startep
            ctrl_updated = True

        if endep > ctrl_end:
            self.upsertData(self._getPricesFromChild(ctrl_end - self.unitsecs, upd_endep, waitDownload))
            ctrl_end = endep
            ctrl_updated = True

        df = self.getData(condList=["EP >= %d" % startep ,"EP <= %d" % endep])
        if ctrl_updated:
            self.updateCtrlTable(ctrl_start, ctrl_end)
        
        return df


    def OLDgetPrices(self, startep, endep, waitDownload=True, buff_size=0):
        upd_startep = startep
        upd_endep = endep
        (minep, maxep) = self.getMinMaxEpoch()
        if startep > maxep and maxep != -1:
            upd_startep = maxep + 1
        else:
            upd_startep -= self.buffer_secs

        if endep < minep and minep != -1:
            upd_endep = minep - 1
        else:
            upd_endep += self.buffer_secs

        ctrl_start = self.ctrl_start
        ctrl_end = self.ctrl_end
        
        df = self.getData(condList=["codename = '%s'" % self.codename,"EP >= %d" % (startep) ,"EP <= %d" % (endep)])
        need_reselect = False
        if len(df.index) == 0:
            if ctrl_start == 0 or ctrl_end == 0 or startep < ctrl_start or endep > ctrl_end:
                need_reselect = True
                self.upsertData(self._getPricesFromChild(upd_startep, upd_endep, waitDownload))
                if startep > 0 and startep < ctrl_start:
                    ctrl_start = startep
                if ctrl_start == 0:
                    ctrl_start = startep

                ctrl_end = max(ctrl_end, endep)
        else:
            new_startep = df.iloc[-1]["ep"]+self.unitsecs
            new_endep = df.iloc[0]["ep"] - self.unitsecs
            
            if startep + buff_size*self.unitsecs < new_endep + 1:
                if upd_startep < ctrl_start or new_endep > ctrl_end:
                    need_reselect = True
                    self.upsertData(self._getPricesFromChild(upd_startep, 
                        new_endep, waitDownload))
                    
                    if upd_startep > 0 and upd_startep < ctrl_start:
                        ctrl_start = upd_startep
                    if ctrl_start == 0:
                        ctrl_start = upd_startep

                    ctrl_end = max(ctrl_end, new_endep)
            if endep - buff_size*self.unitsecs > df.iloc[-1]["ep"]:
                if new_startep < ctrl_start or upd_endep > ctrl_end:
                    need_reselect = True
                    self.upsertData(self._getPricesFromChild(new_startep, 
                        upd_endep, waitDownload))
                    
                    if new_startep > 0 and new_startep < ctrl_start:
                        ctrl_start = new_startep
                    if ctrl_start == 0:
                        ctrl_start = new_startep

                    ctrl_end = max(ctrl_end, upd_endep)
        if need_reselect:
            self.updateCtrlTable(ctrl_start, ctrl_end)
            return self.getData(condList=["EP >= %d" % startep ,"EP <= %d" % endep])
        else:
            return df

    def drop(self):
        self.db.execSql("delete from %s where codename = '%s'" % (self.tablename, self.codename))
        self.db.execSql("delete from %s where codename = '%s' and tablename = '%s';" % (self.ctrl_tablename, self.codename, self.tablename))
        
    def truncate(self):
        self.db.truncateTable(self.tablename)
        self.db.execSql("delete from %s where codename = '%s' and tablename = '%s';" % (self.ctrl_tablename, self.codename, self.tablename))
