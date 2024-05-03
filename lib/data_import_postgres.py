import os, logging, requests, datetime
from dateutil.parser import parse as parsedate
from datetime import datetime
import pandas as pd

import __init__
import lib
import env

from db.pgdf import PgDf

import data_getter
from db.postgresql import PostgreSqlDB
import time
import lib.naming as naming
import json


def getJPXDf():
    url = "https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls"
    tmpdir = "%s/stockanaldata" % (env.conf["tmp_dir"])
    dst_file = '%s/data_j.xls' % tmpdir
    lib.ensureDir(tmpdir)
    
    file_time = lib.dt2epoch(datetime(1900,1,1))
    if os.path.exists(dst_file):
        file_time = lib.dt2epoch(datetime.fromtimestamp(os.path.getmtime(dst_file)))

    try:
        r = requests.head(url)
        url_datetime = lib.dt2epoch(parsedate(r.headers['Last-Modified']))
        if(url_datetime > file_time):
            logging.info("Dowloading data from jpx.co.jp")
            r = requests.get(url)
        
            with open(dst_file, 'wb') as output:
                output.write(r.content)
                os.utime(dst_file, (url_datetime, url_datetime))

    except:
        logging.info("Failed to retrieve the last JPX data")

    if os.path.exists(dst_file):
        return pd.read_excel(dst_file) 
    else:
        return None

def getJPXDfLocal():
    tmpdir = "%s/stockanaldata" % (env.conf["tmp_dir"])
    dst_file = '%s/data_j.xls' % tmpdir
    if os.path.exists(dst_file):
        return pd.read_excel(dst_file) 
    else:
        return None

def importJpxCodes():
    pgdf = PgDf()
    db = PostgreSqlDB()

    for table_name in ["jpx_33gyoshu", 
                        "jpx_17gyoshu", 
                        "jpx_kibo",
                        "codes"]:
        db.dropTable(table_name)
        db.createTable(table_name, "codes")

    df = getJPXDf()
    df.to_sql("jpx_raw", con=pgdf.getEngine(), if_exists="replace", index=False)

    sql = "delete from codes where source = 'jpx';"
    db.execSql(sql)

    sql = """insert into codes(codename, name, source, market, market_detail, market_type, industry33_code)
select distinct concat(コード, '.T') as codename, 
銘柄名 as name, 
'jpx' as source, 
case 
    when 市場・商品区分 = 'ETF・ETN' then 'etf'
    when 市場・商品区分 = 'PRO Market' then 'pro'
    when 市場・商品区分 = 'REIT・ベンチャーファンド・カントリーファンド・インフラファンド' then 'reit'
    when 市場・商品区分 = 'グロース（内国株式）' then 'growth'
    when 市場・商品区分 = 'グロース（外国株式）' then 'growth'
    when 市場・商品区分 = 'スタンダード（内国株式）' then 'standard'
    when 市場・商品区分 = 'スタンダード（外国株式）' then 'standard'
    when 市場・商品区分 = 'プライム（内国株式）' then 'prime'
    when 市場・商品区分 = 'プライム（外国株式）' then 'prime'
    when 市場・商品区分 = '出資証券' then 'shoken'
    else ''
end as market,
市場・商品区分 as market_detail, 
case 
    when 市場・商品区分 = 'グロース（内国株式）' then 'domestic'
    when 市場・商品区分 = 'グロース（外国株式）' then 'overseas'
    when 市場・商品区分 = 'スタンダード（内国株式）' then 'domestic'
    when 市場・商品区分 = 'スタンダード（外国株式）' then 'overseas'
    when 市場・商品区分 = 'プライム（内国株式）' then 'domestic'
    when 市場・商品区分 = 'プライム（外国株式）' then 'overseas'
    else 'other'
end as market_type,
"33業種コード" as industry33_code
from jpx_raw;"""
    db.execSql(sql)
    
    sql = "delete from codes where source = 'manual';"
    db.execSql(sql)

    with open("additional_codes.json", "r") as f:
        data = json.load(f)
        for code in data.keys():
            cols = ["codename", "source"]
            vals = ["'%s'" % code, "'manual'"]
            for col in data[code].keys():
                cols.append(col)
                vals.append("'%s'" % data[code][col])

            """
            cols = ["codename", "source"]
            vals = ["'%s'" % code, "'manual'"]
            if "name" in data[code].keys():
                cols.append("name")
                vals.append("'%s'" % data[code]["name"])
            if "market" in data[code].keys():
                cols.append("market")
                vals.append("'%s'" % data[code]["market"])
            if "market_type" in data[code].keys():
                cols.append("market_type")
                vals.append("'%s'" % data[code]["market_type"])
            """

            sql = "insert into %s(%s) values(%s);" % ("codes", ",".join(cols), ",".join(vals))
            db.execSql(sql)
    logging.info("Completed")


def getRandomCodes(cnt):
    pgdb = PostgreSqlDB()
    sql = """SELECT c1.codename FROM codes AS c1 
    JOIN (SELECT codename FROM codes ORDER BY RAND() LIMIT %d) as c2 
    ON c1.codename=c2.codename""" % cnt
    codes = []
    for (code,) in pgdb.execSql(sql):
        codes.append(code)

    return codes



def importData(granularity, start, end, codes=[],
                random_cnt=0, is_test=False,
                sleep_interval=5):
    if len(start) == 10:
        start = start + "T00:00:00"
        end = end + "T00:00:00"
    startep = lib.str2epoch(start)
    endep = lib.str2epoch(end)
    if random_cnt > 0:
        codes.extend(getRandomCodes(random_cnt))

    if len(codes) == 0:
        db = PostgreSqlDB()
        sql = "select distinct codename from codes;"
        cur = db.execSql(sql)
        for (code,) in cur:
            codes.append(code)

    for instrument in codes:
        logging.info("Getting %s.." % instrument)
        dg = data_getter.getDataGetter(instrument, granularity, is_dgtest=is_test)
        dg.getPrices(startep, endep)
        time.sleep(sleep_interval)

    logging.info("completed")
    



def getCount(code, startep, endep, granularity):
    pgdb = PostgreSqlDB()
    tableName = naming.priceTable(code, granularity)
    cnt = pgdb.countTable(tableName, 
    ["EP >= %d" % startep,
    "EP <= %d" % endep])
    return cnt


if __name__ == "__main__":    
    env.loadConf("default.yaml")
    #importJpxCodes()

    st = lib.dt2str(datetime(year=2016, month=4, day=1))
    ed = lib.dt2str(datetime(year=2024, month=4, day=1))
    #importData("D", st, ed, sleep_interval=3)
    importData("mo1", st, ed, sleep_interval=3)
