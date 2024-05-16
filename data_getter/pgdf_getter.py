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
        self.is_master = is_master
        self.df = pgdf.PgDf(is_master=is_master)
        self.db = pg.PostgreSqlDB(is_master=is_master)
        if self.db.tableExists(self.tablename) == False:
            self.db.createTable(self.tablename, "ohlcv")

    def getMinMaxEpoch(self):
        if self.db.tableExists(self.tablename) == False:
            return (-1, -1)
        (min, max) = self.db.select1rec("select min(EP), max(EP) from %s where codename = '%s';" % (self.tablename, self.codename))
        if min == None:
            min = -1
        if max == None:
            max = -1
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
        
        df = self.getData(condList=["codename = '%s'" % self.codename,"EP >= %d" % (startep) ,"EP <= %d" % (endep)])
        need_reselect = False
        if len(df.index) == 0:
            need_reselect = True
            self.upsertData(self._getPricesFromChild(upd_startep, upd_endep, waitDownload))
        else:
            if startep + buff_size*self.unitsecs < df.iloc[0]["ep"] - self.unitsecs + 1:
                need_reselect = True
                self.upsertData(self._getPricesFromChild(upd_startep, 
                    df.iloc[0]["ep"] - self.unitsecs, waitDownload))
            if endep - buff_size*self.unitsecs > df.iloc[-1]["ep"]:
                need_reselect = True
                self.upsertData(self._getPricesFromChild(df.iloc[-1]["ep"]+self.unitsecs, 
                    upd_endep, waitDownload))
        if need_reselect:
            return self.getData(condList=["EP >= %d" % startep ,"EP <= %d" % endep])
        else:
            return df

    def drop(self):
        self.db.execSql("delete from %s where codename = '%s'" % (self.tablename, self.codename))
        
    def truncate(self):
        self.db.truncateTable(self.tablename)
