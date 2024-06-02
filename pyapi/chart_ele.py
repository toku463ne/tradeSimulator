import lib.indicators as libind


def get_sma_chart_values(name, eps, prices, span):
    x, start_i = libind.sma(prices, span)
    values = []
    for i in range(len(x)):
        item = {}
        item["Date"] = eps[i+start_i]*1000
        item[name] = x[i]
        values.append(item)
    return values

def get_zigzag_chart_values(name, eps, dt, h, l, v, size):
    #newep, newdt, dirs, prices, newv, dists, date_start_index
    xep, _, dirs, x, _, _, _ = libind.zigzag(eps, dt, h, l, v, size)
    values1 = []
    values2 = []
    for i in range(len(x)):
        if abs(dirs[i]) == 2:
            item = {}
            item["Date"] = xep[i]*1000
            item[name] = x[i]
            values1.append(item)
        if abs(dirs[i]) == 1:
            item = {}
            item["Date"] = xep[i]*1000
            item[name] = x[i]
            values2.append(item)
    
    return {"main": values1, "middle": values2}
    
def get_ichimoku_chart_values(name, eps, h, l, c):
    ic = libind.ichimoku(h, l, c)
    icvals = {}
    for key, x in ic.items():
        values = []
        for i in range(len(x)):
            if x[i] is not None:
                item = {}
                item["Date"] = eps[i]*1000
                item[key] = x[i]
                values.append(item)
        icvals[key] = values
    return icvals

def get_backtest_chart_values(trade_name, codename, startep, endep):
    from db.postgresql import PostgreSqlDB
    trades = {}
    pgdb = PostgreSqlDB()
    sql = """SELECT order_id, side, open_epoch, open_price, close_epoch, close_price
FROM trades
WHERE
trade_name = '%s' AND
codename = '%s' AND
open_epoch >= %d and open_epoch <= %d
""" % (trade_name, codename, startep, endep)
    for (order_id, side, open_epoch, open_price, close_epoch, close_price) in pgdb.execSql(sql):
        trades[order_id] = {
            "side": side,
            "open": {"epoch": open_epoch, "price": open_price},
            "close": {"epoch": close_epoch, "price": close_price}
        }

    return trades