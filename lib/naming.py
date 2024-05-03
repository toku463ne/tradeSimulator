import env
import lib


def formatCodeName(codename):
    codename = codename.replace("^","").replace(".","")
    codename = codename.replace("=X", "USD")
    return codename

def priceTable(codename, granularity, tableNamePrefix=""):
    codename = formatCodeName(codename)
    if tableNamePrefix != "":
        return "%s_ohlcv_%s_%s" % (tableNamePrefix, codename, granularity)
    
    return "ohlcv_%s_%s" % (codename, granularity)

def ohlcvTable(granularity):
    return "ohlcv_" + granularity