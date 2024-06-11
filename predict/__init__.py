import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


import importlib

def predict(epoch, strategy_name, strategy_args):
    m = importlib.import_module('strategy.%s' % strategy_name)
    strategy_class = eval("m.%s" % (strategy_name))
    strategy = strategy_class(strategy_args)
    orders = strategy.onTick(epoch)

    order_ids = []
    for order in orders:
        order_ids.append(order.id)

    return order_ids


