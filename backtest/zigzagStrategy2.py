import yaml

import __init__
import backtest
import lib

# date format "%Y-%m-%dT%H:%M:%S"
def run_zigzag(backtest_config):
    with open(backtest_config, "r") as f:
        c = yaml.safe_load(f)
        print(c)
    
    start = lib.dt2epoch(c["start_date"])
    end = lib.dt2epoch(c["end_date"])
    order_stop = lib.dt2epoch(c.get("order_stop", c["end_date"]))
    

    return backtest.run(c["trade_name"], "ZigzagStrategy", c,
                        start, end, order_stop, 
                        c["granularity"],
                        buy_budget=c["buy_budget"], sell_budget=c["sell_budget"])


if __name__ == "__main__":
    import sys
    run_zigzag(sys.argv[1])

