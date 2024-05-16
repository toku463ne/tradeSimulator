from datetime import datetime
from collections import OrderedDict

from strategy import Strategy
from ticker import Ticker
from db.postgresql import PostgreSqlDB
from ticker.zigzag import Zigzag
import lib.tradelib as tradelib
import lib.sqlib as sqlib
import lib
import lib.priceaction as pa
from consts import *

class ZigzagStrategy(Strategy):
    def __init__(self, args):
        self.ticker_codename = args.get("codename", "^N225")
        self.codes = args.get("codes", [])
        self.size = args.get("size", 10)
        self.middle_size = args.get("middle_size", 5)
        self.period = args.get("period", 200)
        self.n_targets = args.get("n_targets", 10)
        self.diff_rate = args.get("diff_percent", 0.02)
        self.max_fund = args.get("max_fund", 1000000)
        self.profit = args.get("profit", 50000)
        self.min_profit = args.get("min_profit", self.profit*0.6)
        self.loss = args.get("loss", 50000)
        self.codenames = args.get("codenames", [])
        self.exclude_codes = args.get("exclude_codes", [])
        self.trade_mode = args.get("trade_mode", TRADE_MODE_ONLY_BUY)
        self.use_master = args.get("use_master", True)
        self.chiko_span = args.get("chiko_span", 26)
        

        # how many times to hold trade on the same peak position
        self.trade_hold_cnt = args.get("trade_hold_cnt", self.middle_size) 
        self.ticker = None
        self.codetickers = {}
        self.zztickers = {}
        self.trade_poses = {}

        

    def getTargetCodes(self, epoch, unitsecs, thresholds={
        "price": 1000,
        "long_candle": True,
        "prefer_recent_peaks": False,
        "mado": True,
        "momiai": True,
        "chiko": 0.8
    }):
        targets = {}
        cond_vals = {}
        granularity = self.timeTicker.granularity
        size = self.size
        middle_size = self.middle_size
        period = self.period
        startep = epoch - unitsecs*period
        chiko_span = self.chiko_span

        conds = []
        conds.append("EP <= %d" % epoch)
        conds.append("EP >= %d" % (int(epoch) - 30*3600*24))

        if len(self.exclude_codes) > 0:
            for exclude_code in self.exclude_codes:
                conds.append("codename NOT LIKE '%s'" % exclude_code)
            
        if len(self.codenames) > 0:
            for code in self.codenames:
                conds.append("codename LIKE '%s'" % code)


        wherestr = sqlib.list2wheresql(conds)


        sql = """WITH r AS (
SELECT
    codename,
    MIN(v) AS vol,
    RANK() OVER (ORDER BY MIN(v) DESC) as rank
FROM 
    ohlcv_d
%s
GROUP BY 1
)
SELECT distinct codename FROM r WHERE rank <= %d
;""" % (wherestr, self.n_targets)
        
        #if lib.epoch2dt(epoch) >= datetime(2021, 11, 30):
        #   print("here")

        for (codename,) in PostgreSqlDB(is_master=self.use_master).execSql(sql):
            z = self.zztickers.get(codename, Zigzag({
                    "codename": codename,
                    "granularity": granularity,
                    "startep": startep,
                    "endep": epoch,
                    "size": size,
                    "middle_size": middle_size,
                    "use_master": self.use_master
                }))
            if z.tick(epoch) == False:
                return {}
            
            t = self.codetickers.get(codename, )

            (zz_ep, zz_dt, zz_dirs, zz_prices, _) = z.getData(startep=startep) # we use zz_dt for debug

            if zz_dt is None:
                continue

            # skip if the price is less than the threshold
            if thresholds["price"] > 0 and zz_prices[-1] < thresholds["price"]:
                continue
            cond_vals["price"] = zz_prices[-1]

            #peaks = sorted(list(zz_prices))
            
            t = self.codetickers.get(codename, Ticker({
                    "codename": codename,
                    "granularity": granularity,
                    "startep": startep - size*unitsecs*2,
                    "endep": epoch,
                    "use_master": self.use_master
                }))
            (_, _, _, h, l, c, _) = t.getPrice(epoch)

            (_, dt, ol, hl, ll, cl, _) = t.getData(n=middle_size+chiko_span)
            if dt is None:
                continue
            max_h = max(hl)
            min_l = min(ll)
            last_dir = zz_dirs[-1]
            last_peak = zz_prices[-1]

            diff = c * self.diff_rate
               

            # check current trend
            trend = 0
            units = self.max_fund/c
            tp_per_unit = self.profit/units
            if last_dir > 0:
                if h < last_peak - tp_per_unit and l < min_l + diff:
                    trend = -1
            if last_dir < 0:
                if l > last_peak + tp_per_unit and h > max_h - diff:
                    trend = 1

            if trend == 0:
                continue

            peaks = []
            for i in range(len(zz_dirs)):
                if zz_dirs[i]*trend > 0:
                    peaks.append(zz_prices[i])

            peaks = sorted(list(peaks))
            
            base = 0
            if trend == 1:
                base = max_h
            elif trend == -1:
                base = min_l
            
            cnt = 0
            s = 0
            last_peak = 0
            for peak in peaks:
                if peak - diff <= base and peak + diff >= base:
                    cnt += 1
                    s += peak
                elif peak - diff > base:
                    break
            
                        
            #tp_diff = 0
            #if trend == 1:
            #    tp_diff = c - tp_below
            #elif trend == -1:
            #    tp_diff = tp_upper - c


            # If there are already more than 2 closer peaks, current price could be the next peak
            if cnt == 0:
                continue

            trade_pos_key = int(s/cnt)

            # If the peak is updated by the last peak, skip the peak
            skip = False
            for j in range(len(zz_prices)):
                k = j+1
                if zz_prices[-k]*trend > (c + diff*trend)*trend:
                    skip = True
                    break

                if k >= 4:
                    break 

            if thresholds["prefer_recent_peaks"] and skip:
                continue

            cond_vals["prefer_recent_peaks"] = skip


            res = pa.checkMado(ol, hl, ll)
            if thresholds["mado"] and res:
                continue
            cond_vals["mado"] = res


            # Check candles
            res = pa.checkMomiai(cl[-middle_size:])
            if thresholds["momiai"] and res:
                continue
            cond_vals["momiai"] = res

            params = pa.checkLastCandle(ol[-middle_size:], hl[-middle_size:], ll[-middle_size:], cl[-middle_size:])
            len_std = params["len_std"]
            hara_rate = params["hara_rate"]
            up_hige_rate = params["up_hige_rate"]
            dw_hige_rate = params["dw_hige_rate"]
            len_avg = params["len_avg"]

            tp_diff = int(len_avg*middle_size/2)
    
            res = len_std > 1.0 and hara_rate >= 0.9
            if thresholds["long_candle"] and res:
                continue
            cond_vals["long_candle"] = res


            cond_vals["chiko"] = 0
            d_rate, u_rate = pa.checkChiko(cl, chiko_span=chiko_span)
            if thresholds["chiko"] > 0:
                if trend == -1:
                    cond_vals["chiko"] = d_rate
                    if d_rate >= thresholds["chiko"]:
                        continue
                elif trend == 1:
                    cond_vals["chiko"] = u_rate
                    if u_rate >= thresholds["chiko"]:
                        continue               
             
            
            # check if current price could be a peak
            targets[codename] = {
                "ticker": t,
                "price": c,
                "tp_diff": tp_diff,
                "trade_pos_key": trade_pos_key,
                "side": -trend,
                "cond_vals": cond_vals
            }
            

        return targets

        
    
    def onTick(self, epoch):
        granularity = granularity = self.timeTicker.granularity
        trade_mode = self.trade_mode
        unitsecs = tradelib.getUnitSecs(granularity)
        if self.ticker == None:
            self.ticker = Ticker({
                "codename": self.ticker_codename, 
                "granularity": self.timeTicker.granularity, 
                "startep": epoch,
                "endep": self.timeTicker.endep,
                "use_master": self.use_master
                })
        
        if self.ticker.tick(epoch) == False:
            return []
        
        trade_poses = self.trade_poses
        trade_hold_cnt = self.trade_hold_cnt
        
        (ep, dt, o, h, l, c, _) = self.ticker.getPrice(epoch)
        if ep == 0:
            return []
        
        targets = self.getTargetCodes(ep, unitsecs, thresholds={
            "price": 1000,
            "long_candle": True,
            "prefer_recent_peaks": True,
            "mado": True,
            "momiai": True,
            "chiko": 0.8
        })

        # update trade pos
        trade_pos_keys = trade_poses.keys()
        for trade_pos_key in trade_pos_keys:
            cnt = trade_poses[trade_pos_key]
            cnt += 1
            if cnt > trade_hold_cnt:
                del trade_poses[trade_pos_key]

        orders = []
        for (codename, target) in targets.items():
            if len(target) == 0:
                continue
            
            side = 0
            if target["side"] == SIDE_BUY and trade_mode == TRADE_MODE_ONLY_BUY or trade_mode == TRADE_MODE_BOTH:
                side = SIDE_BUY
            elif target["side"] == SIDE_SELL and trade_mode == TRADE_MODE_ONLY_SELL or trade_mode == TRADE_MODE_BOTH:
                side = SIDE_SELL

            if side != 0:
                price = target["price"]
                tp_diff = target["tp_diff"]
                t = target["ticker"]
                trade_pos_key = target["trade_pos_key"]

                if trade_pos_key in trade_poses.keys():
                    continue

                takeprofit = 0
                stoploss = 0
                units = self.max_fund/price
                if tp_diff * units < self.min_profit:
                    continue

                takeprofit = price + tp_diff*side
                stoploss = price - tp_diff*side    

                order = self.createStopOrder(epoch, t.dg, side, units,
                    validep=0, takeprofit=takeprofit, stoploss=stoploss, 
                    expiration=(ep + self.size*unitsecs), 
                    desc="Stop Order")
                
                v = target["cond_vals"]
                print("%s price=%f prefer_recent_peaks=%d mado=%d momiai=%d chiko=%f" % (
                    codename, v["price"], v["prefer_recent_peaks"], v["mado"], v["momiai"], v["chiko"]
                ))

                trade_poses[trade_pos_key] = 1
            
                orders.append(order)
    
        self.trade_poses = trade_poses
        return orders