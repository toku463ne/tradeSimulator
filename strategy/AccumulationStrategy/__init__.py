from strategy import Strategy
import lib.tradelib as tradelib
from ticker import Ticker
from consts import *

class AccumulationStrategy(Strategy):
    def __init__(self, args):
        self.codename = args["codename"]
        self.acc_timing = args["acc_timing"]
        self.acc_amount = args.get("acc_amount", 10000)
        self.ticker = None
        self.this_month = 0
        
    def checkDayOnMonth(self, dt, args):
        if dt.day >= args["day"] and dt.month != self.this_month:
            self.this_month = dt.month
            return True
        return False



    # return True/False
    def checkTiming(self, ep, dt, price):
        args = self.acc_timing

        if args["type"] == "day_on_month":
            return self.checkDayOnMonth(dt, args)


    def onTick(self, epoch):
        if self.ticker == None:
            self.ticker = Ticker({
                "codename": self.codename, 
                "granularity": self.timeTicker.granularity, 
                "startep": epoch,
                "endep": self.timeTicker.endep
                })
        
        if self.ticker.tick(epoch) == False:
            return []
        
        (ep, dt, _, _, _, price, _) = self.ticker.getPrice(epoch)
        if ep == 0:
            return []
        
        if self.checkTiming(ep, dt, price) == False:
            return []


        order = self.createMarketOrder(ep,
            self.ticker, SIDE_BUY, self.acc_amount/price)
    
        return [order]