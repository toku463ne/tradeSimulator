import sqlalchemy, logging

import db
import pandas as pd
from env import *
import time
conn_retry = conf["postgresql"]["conn_retry"]

class PgDf(db.DB):
    def __init__(self, is_master=False):
        self.is_master = is_master
        '''
        tableNamePrefix is for testing purpose
        '''
    
    def getEngine(self):
        inf = conf["postgresql"]

        condb = inf["db"]
        if self.is_master == False:
            if conf["is_test"]:
                condb = inf["test_db"]

        connectstr = 'postgresql://%s:%s@%s/%s' % (inf["user"],
        inf["password"],
        inf["host"],
        condb)
        return sqlalchemy.create_engine(connectstr, pool_size=20, max_overflow=0)
        # , poolclass=sqlalchemy.pool.NullPool
        # , pool_recycle=10
        

    def getConn(self):
        return self.getEngine().connect()
        #inf = conf["postgresql"]
        #condb = inf["db"]
        #if self.is_master == False:
        #    if conf["is_test"]:
        #        condb = inf["test_db"]
#
#        conn_string = "host=%s dbname=%s user=%s password=%s" % (
#        inf["host"],
#        condb,
#        inf["user"],
#        inf["password"])
#        return psycopg2.connect(conn_string)

    def read_sql(self, sql):
        time_to_sleep = 1
        df = None
        cnt = 1
        while cnt <= conn_retry:
            try:
                conn = self.getConn()
                df = pd.read_sql(sql, conn)
                conn.close()
            except Exception as e:
                if cnt >= conn_retry:
                    logging.error("tried to connect %d times" % cnt)
                    raise e
                logging.error(e)
                time.sleep(time_to_sleep)
                time_to_sleep += 1
            cnt += 1
        if df is None:
            raise Exception("couldn't get dataframe")
        return df

def read_sql(sql):
    return PgDf().read_sql(sql)