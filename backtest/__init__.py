import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from time_ticker import TimeTicker
from executor import Executor
from portforio import Portoforio
from trade_manager import TradeManager
import importlib

def run(trade_name, strategy_name, strategy_args, 
        start, end, order_stop, 
        granularity,
        buy_budget=1000000, sell_budget=1000000):
    m = importlib.import_module('strategy.%s' % strategy_name)
    strategy_class = eval("m.%s" % (strategy_name))
    strategy = strategy_class(strategy_args)
    ticker = TimeTicker(granularity, start, end)
    executor = Executor()
    portforio = Portoforio(trade_name, buy_budget, sell_budget)
    tm = TradeManager(trade_name, ticker, strategy, executor, portforio)
    result = tm.run(orderstopep=order_stop)

    #print(result)
    return tm.getTrades()
