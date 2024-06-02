import os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

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
        self.diff_rate = args.get("diff_percent", 0.01)
        self.max_fund = args.get("max_fund", 1000000)
        self.profit_rate = args.get("profit_rate", 0.02)
        self.loss_rate = args.get("loss_rate", 0.02)
        self.codenames = args.get("codenames", [])
        self.exclude_codes = args.get("exclude_codes", [])
        self.trade_mode = args.get("trade_mode", TRADE_MODE_ONLY_BUY)
        self.use_master = args.get("use_master", True)
        self.chiko_span = args.get("chiko_span", 26)
        self.min_price = args.get("min_price", 1000)
        self.min_vols = args.get("min_vols", 100000)
        self.thresholds = args.get("thresholds", {
                "long_candle": True,
                "prefer_recent_peaks": False,
                "mado": 0.002,
                "trend_rate": 0.3,
                "chiko": 0.0,
                "reverse_cnt_limit": 0
            })
        self.trade_name = args.get("trade_name", "")
        self.skip_list = []
        self.analize_mode = args.get("analize_mode", False)
        if self.analize_mode:
            self.thresholds = {
                "long_candle": False,
                "prefer_recent_peaks": False,
                "mado": 0.0,
                "trend_rate": 0.0,
                "chiko": 0.0,
                "reverse_cnt_limit": self.middle_size
            }
        self.epiration_limit = args.get("epiration_limit", self.size)
        self.epiration_middle = args.get("epiration_middle", int(self.size/2))      

        # how many times to hold trade on the same peak position
        self.trade_hold_cnt = args.get("trade_hold_cnt", self.middle_size) 
        self.ticker = None
        self.codetickers = {}
        self.zztickers = {}
        self.trade_poses = {}

        self.masterdb = PostgreSqlDB(is_master=self.use_master)
        self.maindb = PostgreSqlDB(is_master=False)
        self.maindb.createTable("zz_strtg_params")

        self.orders = {}

        
    def getTargetCodes(self, epoch):
        conds = []
        conds.append("EP <= %d" % epoch)
        conds.append("EP >= %d" % (int(epoch) - 30*3600*24))
        conds.append("V > 0") # do not count vacations

        if len(self.exclude_codes) > 0:
            for exclude_code in self.exclude_codes:
                conds.append("codename NOT LIKE '%s'" % exclude_code)
            
        inconds = []
        if len(self.codenames) > 0:
            for code in self.codenames:
                inconds.append("codename LIKE '%s'" % code)

        if len(inconds) > 0:
            conds.append("(%s)" % " or ".join(inconds))

        wherestr = sqlib.list2wheresql(conds)


        sql = """WITH s AS (
    SELECT
        codename,
        MIN(v) AS vol,
        AVG(v) as vol_avg,
        MIN(c) AS price,
        COUNT(c) AS cnt
    FROM 
        ohlcv_d
%s
    GROUP BY 
        codename
), r AS (
    SELECT 
        codename, 
        RANK() OVER (ORDER BY vol DESC) AS rank
    FROM 
        s 
    WHERE 
        price >= %f AND 
        cnt >= %d AND
        vol_avg >= %d
) 
SELECT 
    DISTINCT codename 
FROM 
    r 
WHERE 
    rank <= %d
;""" % (wherestr, self.min_price, 10, self.min_vols, self.n_targets)
        
        codes = []
        cnt = 0
        for (code,) in self.masterdb.execSql(sql):
            codes.append(code)
            cnt += 1
            if cnt >= self.n_targets:
                break
        
        return codes




    def checkCode(self, codename, epoch, unitsecs, thresholds={
        "long_candle": True,
        "prefer_recent_peaks": False,
        "mado": 0.002,
        "trend_rate": 0.3,
        "chiko": 0.8
    }):
        cond_vals = {}
        granularity = self.timeTicker.granularity
        size = self.size
        middle_size = self.middle_size
        period = self.period
        startep = epoch - unitsecs*period
        chiko_span = self.chiko_span

        if codename in self.skip_list:
            return
        
        #if lib.epoch2dt(epoch) >= datetime(2022, 11, 22):
        #    print("here")

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
            return
        
        t = self.codetickers.get(codename, )

        (zz_ep, zz_dt, zz_dirs, zz_prices, _) = z.getData(startep=startep) # we use zz_dt for debug

        if zz_dt is None or len(zz_dt) < 3:
            return

        # skip if the price is less than the threshold
        #if thresholds["price"] > 0 and zz_prices[-1] < thresholds["price"]:
        #    return
        #cond_vals["price"] = zz_prices[-1]

        #peaks = sorted(list(zz_prices))
        
        t = self.codetickers.get(codename, Ticker({
                "codename": codename,
                "granularity": granularity,
                "startep": startep - size*unitsecs*2,
                "endep": epoch,
                "use_master": self.use_master
            }))
        (_, _, _, h, l, c, v) = t.getPrice(epoch)
        if v < self.min_vols:
            return
        
        

        (eps, dt, ol, hl, ll, cl, vl) = t.getData(n=middle_size+chiko_span)
        if dt is None:
            self.skip_list.append(codename)
            return
        
        
        if len(ol) < middle_size:
            return

        max_h = max(hl[chiko_span:])
        min_l = min(ll[chiko_span:])

        if (min_l != l and min_l != ll[-2]) and (max_h != h and max_h != hl[-2]):
            return

        last_dir = zz_dirs[-1]
        last_peak = zz_prices[-1]
        leg_len = abs(last_peak - zz_prices[-2])
        diff = c * self.diff_rate

        tp_diff = c*self.profit_rate
        if tp_diff > leg_len/2:
            return



        # check current trend
        trend = 0
        if last_dir > 0:
            if ll[-middle_size] == min_l or ll[-middle_size+1] == min_l:
                trend = 1
            elif h + diff < last_peak:
                trend = -1
        elif last_dir < 0:
            if hl[-middle_size] == max_h or hl[-middle_size+1] == max_h:
                trend = -1
            elif l - diff > last_peak:
                trend = 1

        if trend == 0:
            return
        
        if trend == 1 and l <= min(ll[-2:]):
            return
        if trend == -1 and h >= max(hl[-2:]):
            return


        # check number of candles with volume
        if zz_dirs[-1]*trend < 0:
            last_peak_ep = zz_ep[-1]
        else:
            last_peak_ep = zz_ep[-2]
        candle_cnt = 0
        for i in range(middle_size+chiko_span):
            j = i + 1
            if eps[-j] < last_peak_ep:
                break
            if vl[-j] > 0:
                candle_cnt += 1
            
        # in case it is less than middle, we consider not enough
        if candle_cnt < middle_size:
            return

        if last_peak_ep >= eps[-middle_size]:
            if trend == 1 and min_l != last_peak and min_l < last_peak + diff:
                return
            
            if trend == -1 and max_h != last_peak and max_h > last_peak - diff:
                return


        
        #if trend > 0 and zz_dirs[-1] < 0:
        #    if max_h >= last_peak:
        #        return
        #if trend < 0 and zz_dirs[-1] > 0:
        #    if min_l <= last_peak:
        #        return

        #peaks = []
        #for i in range(len(zz_dirs)):
        #    if i > 0:
        #        if zz_dirs[i] > zz_dirs[i-1] and zz_prices[i] > zz_prices[i-1] or \
        #            zz_dirs[i] < zz_dirs[i-1] and zz_prices[i] < zz_prices[i-1]: 
        #            peaks.append(zz_prices[i])

        peaks = sorted(list(zz_prices))
        
        base = 0
        if trend == 1:
            base = max_h
        elif trend == -1:
            base = min_l
        
        cnt = 0
        s = 0
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
            return

        trade_pos_key = int(s/cnt)
        #diff2 = abs(c - trade_pos_key)*2
        if abs(c - trade_pos_key) > tp_diff:
            return

        # check if some recent peaks touched the trade_pos_key
        reversed_cnt = 0
        for i in range(middle_size*2-2):
            j = i + 3
            if trend > 0 and hl[-j] + diff >= trade_pos_key:
                reversed_cnt += 1
                
            if trend < 0 and ll[-j] - diff <= trade_pos_key:
                reversed_cnt += 1


        cond_vals["reversed_cnt"] = reversed_cnt
        if reversed_cnt > thresholds["reverse_cnt_limit"]:
            return


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
            return

        cond_vals["prefer_recent_peaks"] = skip


        mado = pa.checkMado(ol, hl, ll)
        if thresholds["mado"] > 0 and mado > thresholds["mado"]:
            return
        cond_vals["mado"] = mado


        # Check candles
        trend_rate, has_trend = pa.checkTrendRate(hl[-middle_size:],ll[-middle_size:],cl[-middle_size:])
        if thresholds["trend_rate"] > 0 and ((trend_rate < thresholds["trend_rate"]) or has_trend == False):
            return
        cond_vals["trend_rate"] = trend_rate

        if has_trend and trend_rate*trend < 0:
            return

        params = pa.checkLastCandle(ol[-middle_size:], hl[-middle_size:], ll[-middle_size:], cl[-middle_size:])
        if params is None:
            return
        len_std = params["len_std"]
        hara_rate = params["hara_rate"]
        up_hige_rate = params["up_hige_rate"]
        dw_hige_rate = params["dw_hige_rate"]
        len_avg = params["len_avg"]

        cond_vals["len_std"] = len_std
        cond_vals["hara_rate"] = hara_rate
        cond_vals["up_hige_rate"] = up_hige_rate
        cond_vals["dw_hige_rate"] = dw_hige_rate
        cond_vals["len_avg"] = len_avg


        res = len_std > 1.0 and hara_rate >= 0.9
        if thresholds["long_candle"] and res:
            return
        cond_vals["long_candle"] = bool(res)


        cond_vals["chiko"] = 0
        d_rate, u_rate = pa.checkChiko(cl, chiko_span=chiko_span)
        if trend == -1:
            cond_vals["chiko"] = d_rate
            if thresholds["chiko"] > 0 and d_rate >= thresholds["chiko"]:
                return
        elif trend == 1:
            cond_vals["chiko"] = u_rate
            if thresholds["chiko"] > 0 and u_rate >= thresholds["chiko"]:
                return

        return {
            "ticker": t,
            "price": c,
            "tp_diff": tp_diff,
            "trade_pos_key": trade_pos_key,
            "trend": trend,
            "cond_vals": cond_vals
        }
            
    def getOrder(self, codename, epoch, unitsecs, target):
        trade_mode = self.trade_mode
        trade_poses = self.trade_poses.get(codename, {})
        trade_hold_cnt = self.trade_hold_cnt
        # update trade pos
        trade_pos_keys = trade_poses.keys()
        for trade_pos_key in trade_pos_keys:
            cnt = trade_poses[trade_pos_key]
            cnt += 1
            if cnt > trade_hold_cnt:
                del trade_poses[trade_pos_key]


        if len(target) == 0:
            return
        
        target_side = -target["trend"]
        side = 0
        if target_side == SIDE_BUY and (trade_mode == TRADE_MODE_ONLY_BUY or trade_mode == TRADE_MODE_BOTH):
            side = SIDE_BUY
        elif target_side == SIDE_SELL and (trade_mode == TRADE_MODE_ONLY_SELL or trade_mode == TRADE_MODE_BOTH):
            side = SIDE_SELL

        if side == 0:
            return

        price = target["price"]
        tp_diff = target["tp_diff"]
        t = target["ticker"]
        trade_pos_key = target["trade_pos_key"]

        if trade_pos_key in trade_poses.keys():
            return

        takeprofit = 0
        stoploss = 0
        units = self.max_fund/price
        #if tp_diff * units < self.min_profit:
        #    return

        takeprofit = price + tp_diff*side
        #stoploss = price - tp_diff*side
        stoploss = float(trade_pos_key) - tp_diff*side
        diff = price * self.diff_rate    

        order = self.createStopOrder(epoch, t, side, units, price, name=self.trade_name,
            validep=0, takeprofit=takeprofit, stoploss=stoploss, 
            desc="op:%f line:%d diff:%f tp:%f" % (price, trade_pos_key, diff, tp_diff))
        
        #v = target["cond_vals"]
        #print("%s prefer_recent_peaks=%d mado=%d trend_rate=%d chiko=%f" % (
        #    codename, v["prefer_recent_peaks"], v["mado"], v["trend_rate"], v["chiko"]
        #))

        trade_poses[trade_pos_key] = 1
        self.trade_poses[codename] = trade_poses

        return order

    # codename, epoch, dt, i+1, target
    def insertTradeInfo(self, order_id, codename, epoch, dt, rank, target):
        self.maindb.execSql("DELETE FROM zz_strtg_params WHERE order_id = '%s';" % order_id)

        con = target["cond_vals"]
        sql = """INSERT INTO zz_strtg_params(
    order_id, codename, EP, DT, price, trend, vol_rank, trade_pos_key,
    tp_diff, prefer_recent_peaks, mado, 
    trend_rate, long_candle, chiko,
    len_std, hara_rate, up_hige_rate, dw_hige_rate, len_avg, reversed_cnt
)
VALUES('%s', '%s', %d, '%s', %f, %d, %d, %d,
%f, %d, %f, 
%f, %d, %f,
%f, %f, %f, %f, %f, %d);
""" % (
    order_id, codename, epoch, dt, target["price"], target["trend"], rank, target["trade_pos_key"],
    target["tp_diff"], con["prefer_recent_peaks"], con["mado"], 
    con["trend_rate"], con["long_candle"], con["chiko"],
    con["len_std"], con["hara_rate"], con["up_hige_rate"], con["dw_hige_rate"], con["len_avg"], con["reversed_cnt"]
)
        self.maindb.execSql(sql)

    
    def onTick(self, epoch):
        granularity = granularity = self.timeTicker.granularity
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
        
        
        (ep, dt, _, _, _, _, _) = self.ticker.getPrice(epoch)
        if ep == 0:
            return []
        
        codes = self.getTargetCodes(ep)
        orders = []
        #for codename in codes:
        for i in range(len(codes)):
            codename = codes[i]
            target = self.checkCode(codename, ep, unitsecs, thresholds=self.thresholds)
            if target is not None:
                order = self.getOrder(codename, ep, unitsecs, target)
                if order is not None:
                    local_order_id = order.localId
                    if self.analize_mode:
                        self.insertTradeInfo(local_order_id, codename, epoch, dt, i+1, target)
                    orders.append(order)
    
        return orders
    
    def bkonTick(self, epoch):
        granularity = self.timeTicker.granularity
        unitsecs = tradelib.getUnitSecs(granularity)
        if self.ticker is None:
            self.ticker = Ticker({
                "codename": self.ticker_codename, 
                "granularity": self.timeTicker.granularity, 
                "startep": epoch,
                "endep": self.timeTicker.endep,
                "use_master": self.use_master
            })
        
        if not self.ticker.tick(epoch):
            return []
        
        (ep, dt, _, _, _, _, _) = self.ticker.getPrice(epoch)
        if ep == 0:
            return []
        
        codes = self.getTargetCodes(ep)
        orders = []

        def process_code(codename):
            target = self.checkCode(codename, ep, unitsecs, thresholds=self.thresholds)
            if target is not None:
                order = self.getOrder(codename, ep, unitsecs, target)
                if order is not None:
                    local_order_id = order.localId
                    if self.analize_mode:
                        self.insertTradeInfo(local_order_id, codename, epoch, dt, codes.index(codename) + 1, target)
                    return order
            return None

        with ThreadPoolExecutor(max_workers=len(codes)) as executor:
            futures = {executor.submit(process_code, codename): codename for codename in codes}
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    orders.append(result)
        
        return orders



    def onSignal(self, epoch, event):
        if event.cmd != ESTATUS_TRADE_OPENED:
            return 

        _id = event.id
        order = self.orders.get(_id, {"count": 0, "event": event})
        cnt = order["count"]
        cnt += 1
        
        if cnt >= self.epiration_limit:
            if _id in self.orders.keys():
                del self.orders[_id]
            return self.cancelOrder(epoch, _id)

        if cnt >= self.epiration_middle:
            side = event.side
            price = event.price
            (_, _, _, _, _, cur_price, _) = event.dg.getPrice(epoch)
            if cur_price*side > price*side:
                if _id in self.orders.keys():
                    del self.orders[_id]
                return self.cancelOrder(epoch, _id)
        
        order["count"] = cnt
        



if __name__ == "__main__":
    from time_ticker import TimeTicker
    from executor import Executor
    from trade_manager import TradeManager
    from portforio import Portoforio
    st = lib.str2epoch("2018-01-01T00:00:00")
    ed = lib.str2epoch("2024-01-01T00:00:00")
    os = lib.str2epoch("2024-01-01T00:00:00")
    
    sql = "SELECT distinct codename from bk_trades WHERE trade_name = 'anal_zigzag';"
    codes = []
    for (codename,) in PostgreSqlDB().execSql(sql):
        if codename in ["4385.T", "5253.T"]:
            continue
        codes.append(codename)
    args = {
        "codenames": codes,
        "use_master": True,
        "analize_mode": True,
        "n_targets": 1000,
        "trade_name": "zzanal2"}
    strategy = ZigzagStrategy(args)
    ticker = TimeTicker("D", st, ed)
    executor = Executor()
    portforio = Portoforio("zzanal2", 1000000000, 1000000000)
    tm = TradeManager("Anal zigzag strategy", ticker, strategy, executor, portforio)
    report = tm.run(endep=ed, orderstopep=os)
        