from datetime import datetime

from strategy import Strategy
from ticker import Ticker
from db.postgresql import PostgreSqlDB
from ticker.peaks import Peaks
import lib.tradelib as tradelib
import lib.sqlib as sqlib
import lib
from consts import *

class PeaksStrategy(Strategy):
    def __init__(self, args):
        self.ticker_codename = args.get("codename", "^N225")
        self.codes = args.get("codes", [])
        self.size = args.get("size", 10)
        self.period = args.get("period", 365)
        self.n_targets = args.get("n_targets", 10)
        self.diff_rate = args.get("diff_percent", 0.02)
        self.max_fund = args.get("max_fund", 1000000)
        self.max_fund = args.get("profit", 50000)
        self.max_fund = args.get("loss", 50000)
        self.codenames = args.get("codenames", [])
        self.exclude_codes = args.get("exclude_codes", [])
        self.trade_mode = args.get("trade_mode", TRADE_MODE_ONLY_BUY)
        self.ticker = None
        self.subtickers = {}
        self.peaktickers = {}

        

    def getTargetCodes(self, epoch):
        buy_targets = {}
        sell_targets = {}
        granularity = self.timeTicker.granularity
        unitsecs = tradelib.getUnitSecs(granularity)
        startep = self.timeTicker.startep
        endep = self.timeTicker.endep

        conds = []
        if len(self.exclude_codes) > 0:
            conds.append("codename not in ('%s')" % "','".join(self.exclude_codes))
        if len(self.codenames) > 0:
            conds.append("codename in ('%s')" % "','".join(self.codenames))


        wherestr = sqlib.list2wheresql(conds)


        sql = """WITH r AS (
SELECT
    codename,
    date_trunc('month', dt) AS month,
    ceil(SUM(v)/1000000) AS vol,
    RANK() OVER (PARTITION BY date_trunc('month', dt) ORDER BY SUM(v) DESC) as rank
FROM 
    ohlcv_d
%s
GROUP BY 1,2
)
SELECT distinct codename FROM r WHERE rank <= %d
;""" % (wherestr, self.n_targets)
        

        if lib.epoch2dt(epoch) >= datetime(2021, 10, 19):
            print("here")

        for (codename,) in PostgreSqlDB().execSql(sql):
            p = self.peaktickers.get(codename, Peaks({
                    "codename": codename,
                    "granularity": granularity,
                    "size": self.size,
                    "period": self.period,
                    "startep": startep,
                    "endep": endep
                }))
            if p.tick(epoch) == False:
                return None, None

            peaks = sorted(list(p.data.price))

            t = self.subtickers.get(codename, Ticker({
                    "codename": codename,
                    "granularity": granularity,
                    "startep": startep - self.size*unitsecs*2,
                    "endep": endep
                }))
            (_, _, _, h, l, c, _) = t.getPrice(epoch)

            diff = c * self.diff_rate

            cnt = 0
            for peak in peaks:
                if peak - diff <= h and peak + diff >= h:
                    cnt += 1
                elif peak - diff <= l and peak + diff >= l:
                    cnt += 1
                elif peak - diff > c:
                    break

            # If there are already more than 2 closer peaks, current price could be the next peak
            if cnt >= 1:
                (_, _, _, hl, ll, _, _) = t.getData(n=self.size)
                
                # check if current price could be a peak
                if max(hl) < h + diff:
                    sell_targets[codename] = (t,c)
                if min(ll) > l - diff:
                    buy_targets[codename] = (t,c)


        return buy_targets, sell_targets

        
    
    def onTick(self, epoch):
        if self.ticker == None:
            self.ticker = Ticker({
                "codename": self.ticker_codename, 
                "granularity": self.timeTicker.granularity, 
                "startep": epoch,
                "endep": self.timeTicker.endep
                })
        
        if self.ticker.tick(epoch) == False:
            return []
        
        (ep, dt, o, h, l, c, _) = self.ticker.getPrice(epoch)
        if ep == 0:
            return []
        
        buy_targets, sell_targets = self.getTargetCodes(ep)
        targets = {"buy": buy_targets, "sell": sell_targets}

        orders = []
        for (trade_mode, target) in targets.items():
            if len(target) == 0:
                continue
            side = 0
            if trade_mode == "buy" and self.trade_mode == TRADE_MODE_ONLY_BUY or self.trade_mode == TRADE_MODE_BOTH:
                side = SIDE_BUY
            if trade_mode == "sell" and self.trade_mode == TRADE_MODE_ONLY_SELL or self.trade_mode == TRADE_MODE_BOTH:
                side = SIDE_SELL

            if side != 0:
                for (_, (t, price)) in target.items():
                    units = self.max_fund/price
                    takeprofit = price + self.profit/units
                    stoploss = price - self.loss/units

                    order = self.createStopOrder(epoch, t.dg, side, units,
                        validep=0, takeprofit=takeprofit, stoploss=stoploss, 
                        expiration=(ep + self.size*self.unitsecs), 
                        desc="Stop Order")
                
                    orders.append(order)
    
        return orders