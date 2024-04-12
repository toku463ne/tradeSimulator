from data_getter.mydf_getter import MyDfGetter
from data_getter import DataGetter
import lib.naming as naming
import datetime
import pandas as pd
import lib

class MyGetter(DataGetter):
    def __init__(self,childDG, tableNamePrefix="", is_dgtest=False):
        self.name = "mygetter_%s_%s" % (childDG.codename, childDG.granularity)
        self.codename = childDG.codename
        self.granularity = childDG.granularity
        self.tableName = naming.priceTable(childDG.codename, childDG.granularity, tableNamePrefix)
        self.mydf = MyDfGetter(childDG, tableNamePrefix, is_dgtest=is_dgtest)
        self.unitsecs = self.mydf.unitsecs

    def getPrices(self, startep, endep, waitDownload=True, buff_size=0):
        df = self.mydf.getPrices(startep, endep, waitDownload, buff_size=buff_size)
        eps = df.EP.values.tolist()
        #dt = df.DT.values.tolist()
        #dt = df.DT.values.astype(datetime.datetime)
        #dt = pd.Timestamp(df.DT.values)
        dt = []
        for dt64 in df.DT.values:
            dt.append(lib.npdt2dt(dt64))
        o = df.O.values.tolist()
        h = df.H.values.tolist()
        l = df.L.values.tolist()
        c = df.C.values.tolist()
        v = df.V.values.tolist()
        return (eps, dt, o, h, l, c, v)
        
    def drop(self):
        self.mydf.drop()
        
    def truncate(self):
        self.mydf.truncate()
