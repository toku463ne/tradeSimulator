import backtest
import lib

# date format "%Y-%m-%dT%H:%M:%S"
def run_simple_market(trade_name,
        codename, 
        granularity, 
        profit, 
        startstr, endstr, orderstopstr="",
        buy_budget=1000000, sell_budget=1000000):
    start = lib.str2epoch(startstr)
    end = lib.str2epoch(endstr)
    if orderstopstr == "":
        orderstopstr = endstr
    order_stop = lib.str2epoch(orderstopstr)
    return backtest.run(trade_name, "SimpleMarketStrategy", 
                        {"codename": codename, 
                         "granularity": granularity, 
                         "profit": profit}, 
                        start, end, order_stop, 
                        granularity,
                        buy_budget=buy_budget, sell_budget=sell_budget)

