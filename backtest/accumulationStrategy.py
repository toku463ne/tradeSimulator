import backtest
import lib

# date format "%Y-%m-%dT%H:%M:%S"
def run_day_on_month(trade_name,
                    codename, 
                    granularity, 
                    startstr, endstr, orderstopstr,
                    acc_amount=10000, 
                    day=1,
                    buy_budget=1000000, sell_budget=1000000):
    strategy_args = {"codename": codename,"acc_amount": acc_amount,"acc_timing": {"type": "day_on_month","day": day}}
    start = lib.str2epoch(startstr)
    end = lib.str2epoch(endstr)
    order_stop = lib.str2epoch(orderstopstr)
    return backtest.run(trade_name, "AccumulationStrategy", strategy_args, 
                        start, end, order_stop, 
                        granularity,
                        buy_budget=buy_budget, sell_budget=sell_budget)

