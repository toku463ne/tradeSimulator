from data_getter.pgdf_getter import PgDfGetter
from data_getter import DataGetter
import lib

class PgGetter(DataGetter):
    def __init__(self,childDG, is_dgtest=False):
        self.name = "pggetter_%s_%s" % (childDG.codename, childDG.granularity)
        self.codename = childDG.codename
        self.granularity = childDG.granularity
        self.pgdf = PgDfGetter(childDG, is_dgtest=is_dgtest)
        self.unitsecs = self.pgdf.unitsecs

    #def getPrices(self, startep, endep, waitDownload=True, buff_size=0):
    #    df = self.pgdf.getPrices(startep, endep, waitDownload, buff_size=buff_size)
    def getPrices(self, startep, endep, waitDownload=True):
        df = self.pgdf.getPrices(startep, endep, waitDownload)
        eps = df.ep.values.tolist()
        #dt = df.DT.values.tolist()
        #dt = df.DT.values.astype(datetime.datetime)
        #dt = pd.Timestamp(df.DT.values)
        dt = []
        for dt64 in df.dt.values:
            dt.append(lib.npdt2dt(dt64))
        o = df.o.values.tolist()
        h = df.h.values.tolist()
        l = df.l.values.tolist()
        c = df.c.values.tolist()
        v = df.v.values.tolist()
        return (eps, dt, o, h, l, c, v)
        
    def drop(self):
        self.pgdf.drop()
        
    def truncate(self):
        self.pgdf.truncate()

    def getCtrlInfo(self):
        return self.pgdf.getCtrlInfo()
