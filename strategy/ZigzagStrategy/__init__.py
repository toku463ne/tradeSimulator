"""
TODO:
dai in sen
mado + sita kasa
momiai indicator

"""

import os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

MAX_THREADS = 10

from strategy import Strategy
from ticker import Ticker
from db.postgresql import PostgreSqlDB
from ticker.zigzag import Zigzag
import lib.tradelib as tradelib
import lib.sqlib as sqlib
import lib
import lib.priceaction as pa
from consts import *
import env
from analyze.zigzagStrategy.predictor import ZzCodePredictor

class ZigzagStrategy(Strategy):
    def __init__(self, args):
        self.ticker_codename = args.get("codename", "^N225")
        self.codes = args.get("codes", [])
        self.size = args.get("size", 10)
        self.middle_size = args.get("middle_size", 5)
        self.period = args.get("period", 180)
        self.n_targets = args.get("n_targets", 100)
        self.diff_rate = args.get("diff_percent", 0.01)
        self.max_fund = args.get("max_fund", 1000000)
        self.profit_rate = args.get("profit_rate", 0.05)
        self.loss_rate = args.get("loss_rate", 0.015)
        self.codenames = args.get("codenames", [])
        self.exclude_codes = args.get("exclude_codes", [])
        self.trade_mode = args.get("trade_mode", TRADE_MODE_BOTH)
        self.use_master = args.get("use_master", True)
        self.chiko_span = args.get("chiko_span", 26)
        self.min_price = args.get("min_price", 1000)
        self.min_vols = args.get("min_vols", 100000)
        self.debug_date = args.get("debug_date", None)
        self.trade_name = args["trade_name"]
        self.ref_trade_name = args.get("ref_trade_name", self.trade_name)
        self.skip_list = []
        self.analize_mode = args.get("analize_mode", False)
        self.epiration_limit = args.get("epiration_limit", self.size)
        self.epiration_middle = args.get("epiration_middle", int(self.middle_size/2)+1)      

        # how many times to hold trade on the same peak position
        self.trade_hold_cnt = args.get("trade_hold_cnt", self.middle_size) 
        self.ticker = None
        self.codetickers = {}
        self.zztickers = {}
        self.trade_poses = {}

        self.masterdb = PostgreSqlDB(is_master=self.use_master)
        self.maindb = PostgreSqlDB(is_master=False)
        self.maindb.createTable("zz_strtg_params")
        self.maindb.createTable("zz_probas")

        self.maindb.execSql("delete from zz_strtg_params where order_id like '%%%s';" % self.trade_name)
        self.maindb.execSql("delete from zz_probas where order_id like '%%%s';" % self.trade_name)

        self.predictor = ZzCodePredictor(self.ref_trade_name)

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



    def checkCode(self, codename, epoch, unitsecs, ticker, config_path=""):
        cond_vals = {}
        granularity = self.timeTicker.granularity
        size = self.size
        middle_size = self.middle_size
        period = self.period
        startep = epoch - unitsecs*period
        chiko_span = self.chiko_span

        if codename in self.skip_list:
            return
        
        if self.debug_date is not None and lib.epoch2dt(epoch) == self.debug_date:
            print("here")

        z = self.zztickers.get(codename, Zigzag({
                "codename": codename,
                "granularity": granularity,
                "startep": startep,
                "endep": epoch,
                "size": size,
                "middle_size": middle_size,
                "use_master": self.use_master,
                "config_path": config_path
            }))
        if z.tick(epoch) == False:
            return
        

        (zz_ep, zz_dt, zz_dirs, zz_prices, _) = z.getData(startep=startep) # we use zz_dt for debug

        if zz_dt is None or len(zz_dt) < 2:
            return

        
        (_, _, _, h, l, c, v) = ticker.getPrice(epoch)
        if v < self.min_vols:
            return
        
        if v == 0:
            return

        (eps, dt, ol, hl, ll, cl, vl) = ticker.getData(n=middle_size+chiko_span)
        if dt is None:
            self.skip_list.append(codename)
            return
        
        
        if len(ol) < middle_size:
            return
        
        if len(eps) <= chiko_span:
            return
        
        max_h = max(hl[chiko_span:])
        min_l = min(ll[chiko_span:])

        #if (min_l != l and min_l != ll[-2]) and (max_h != h and max_h != hl[-2]):
        #    return

        if len(zz_prices) < 3:
            return

        tp_diff = c*self.profit_rate
        
        recent_range = (max(hl[-size:]) - min(ll[-size:]))*1.0
        tp_diff = min(tp_diff, recent_range/2.0)
        tp_diff2 = max(max(hl[-size:])-c,c-min(ll[-size:]))*1.0/2.0
        tp_diff = min(tp_diff, tp_diff2)
        

        last_dir = zz_dirs[-1]
        last_peak = zz_prices[-1]
        diff = min(c * self.diff_rate, recent_range*0.1)

        

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
        for i in range(middle_size):
            j = i + 1
            if eps[-j] < last_peak_ep:
                break
            if vl[-j] > 0:
                candle_cnt += 1
            
        # in case it is less than middle, we consider not enough
        if candle_cnt < middle_size-2:
            return
        

        # not enough data
        candle_cnt = 0
        for i in range(size):
            if vl[-i-1] > 0:
                candle_cnt += 1
        if candle_cnt < size-2:
            return


        if last_peak_ep >= eps[-middle_size]:
            if trend == 1 and min_l != last_peak and min_l < last_peak + diff:
                return
            
            if trend == -1 and max_h != last_peak and max_h > last_peak - diff:
                return


        
        if trend == -1:
            peaks = sorted(zz_prices[-3:])
            old_peaks = sorted(zz_prices[:-3])
        else:
            peaks = sorted(zz_prices[-3:], reverse=True)
            old_peaks = sorted(zz_prices[:-3], reverse=True)
        
        ma = max(peaks)
        mi = min(peaks)
        peaks.extend(old_peaks)
        
        trade_pos_key = 0
        for i in range(len(peaks)):
            peak = peaks[i]

            # from the 3rd peak we only consider peaks above recent peaks
            if i >= 3:
                if peak >= mi and peak <= ma:
                    continue

            if c*trend > peak*trend:
                if (peak + diff*trend)*trend > c*trend:
                    trade_pos_key = peak
                break
            
            trade_pos_key = peak


        if trade_pos_key == 0:
            return

        if abs(c - trade_pos_key) > tp_diff:
            return


        # check if some recent peaks touched the trade_pos_key
        reversed_cnt = 0
        for i in range(2, size):
            if trend > 0 and hl[-i] + diff >= trade_pos_key:
                reversed_cnt += 1
            if trend < 0 and ll[-i] - diff <= trade_pos_key:
                reversed_cnt += 1


        cond_vals["reversed_rate"] = (reversed_cnt*1.0 / size)
      

        # if the peak is broken by the recent price
        broken_cnt = 0
        for i in range(1, size):
            if (ll[-i-1] > trade_pos_key) and (ll[-i] < trade_pos_key-diff) or \
               (hl[-i-1] < trade_pos_key) and (hl[-i] > trade_pos_key+diff) or \
                (ll[-i] < trade_pos_key-diff) and (hl[-i] > trade_pos_key+diff):
                broken_cnt += 1

        cond_vals["peak_broken_rate"] = broken_cnt*1.0/(size*1.0)
        #cond_vals["peak_broken"] = (min(ll[-size:]) < trade_pos_key-diff) and (max(hl[-size:]) > trade_pos_key+diff)



        mado = pa.checkMado(ol, hl, ll, cl)
        cond_vals["mado"] = mado

        acc = pa.checkAccumulation(ol, cl)
        cond_vals["acc"] = acc

        # Check candles
        trend_rate, has_trend = pa.checkTrendRate(hl[-middle_size:],ll[-middle_size:],cl[-middle_size:])
        cond_vals["trend_rate"] = trend_rate

        if has_trend and trend_rate*trend < 0:
            return

        params = pa.checkLastCandle(ol[-size:], hl[-size:], ll[-size:], cl[-size:])
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


        cond_vals["chiko"] = 0
        d_rate, u_rate = pa.checkChiko(cl, chiko_span=chiko_span)
        if trend == -1:
            cond_vals["chiko"] = d_rate
        elif trend == 1:
            cond_vals["chiko"] = u_rate

        if trend == -1:
            price = min(trade_pos_key + diff, c)
        if trend == 1:
            price = max(trade_pos_key - diff, c)

        cond_vals["tp_diff"] = tp_diff

        cond_vals["momiai1"] = pa.checkMomiai(hl[-middle_size:], ll[-middle_size:], n_targets=1)
        cond_vals["momiai2"] = pa.checkMomiai(hl[-size-1:-1], ll[-size-1:-1], n_targets=1)

        last, mi, ma = pa.distFromAvg(cl[-size:])
        cond_vals["avg_dist_last"] = last
        cond_vals["avg_dist_max"] = ma
        cond_vals["avg_dist_min"] = mi

        side = 0
        if price > trade_pos_key:
            side = SIDE_BUY
        if price < trade_pos_key:
            side = SIDE_SELL
        probas = self.predictor.predict_trade(codename, side, cond_vals)
        
        
        #cond_vals["proba"] = proba
        #cond_vals["accuracy"] = accuracy

        
        return {
            "codename": codename,
            "ticker": ticker,
            "price": price,
            "side": side,
            "tp_diff": tp_diff,
            "trade_pos_key": trade_pos_key,
            "trend": trend,
            "cond_vals": cond_vals,
            "probas": probas
        }
            
    def getOrder(self, epoch, target, unitsecs):
        trade_mode = self.trade_mode
        
        if len(target) == 0:
            return None, None
        
        price = target["price"]
        tp_diff = target["tp_diff"]
        t = target["ticker"]
        trade_pos_key = target["trade_pos_key"]
        target_side = target["side"]


        #target_side = -target["trend"]
        side = 0
        if target_side == SIDE_BUY and (trade_mode == TRADE_MODE_ONLY_BUY or trade_mode == TRADE_MODE_BOTH):
            side = SIDE_BUY
        elif target_side == SIDE_SELL and (trade_mode == TRADE_MODE_ONLY_SELL or trade_mode == TRADE_MODE_BOTH):
            side = SIDE_SELL

        if side == 0:
            return None, None
        

        takeprofit = 0
        stoploss = 0
        units = self.max_fund/price

        stoploss = float(trade_pos_key) - tp_diff*side
        diff = abs(price - stoploss)
        takeprofit = price + diff*side

        #diff = price * self.diff_rate
        order_expiration = epoch + unitsecs*3    

        order = self.createStopOrder(epoch, t, side, units, price, name=self.trade_name,
            validep=0, takeprofit=takeprofit, stoploss=stoploss, order_expiration=order_expiration,
            desc="op:%f line:%d diff:%f tp:%f" % (price, trade_pos_key, diff, tp_diff), args=target["cond_vals"])
        

        return order, trade_pos_key
    
    def insertProba(self, order_id, probas):
        sql = """INSERT INTO zz_probas(
order_id, 
proba_all, proba_group, proba_kobetsu)
VALUES('%s', %f, %f, %f)
;""" % (order_id, 
        probas["all"], probas["group"], probas["kobetsu"])

        try:
            self.maindb.execSql(sql)
        except Exception as e:
            print(e)


    # codename, epoch, dt, i+1, target
    def insertTradeInfo(self, order_id, codename, epoch, dt, rank, target, order):
        #self.maindb.execSql("DELETE FROM zz_strtg_params WHERE order_id = '%s';" % order_id)

        con = target["cond_vals"]
        sql = """INSERT INTO zz_strtg_params(
    order_id, codename, EP, DT, price, 
    side, takeprofit_price, stoploss_price,
    trend, vol_rank, trade_pos_key,
    tp_diff, peak_broken_rate, mado, acc,
    trend_rate, chiko,
    len_std, hara_rate, up_hige_rate, dw_hige_rate, len_avg, 
    reversed_rate, momiai1, momiai2,
    avg_dist_last, avg_dist_min, avg_dist_max
)
VALUES('%s', '%s', %d, '%s', %f, 
%d, %f, %f,
%d, %d, %d,
%f, %f, %f, %f,
%f, %f,
%f, %f, %f, %f, %f, 
%d, %f, %f,
%f, %f, %f)
;""" % (
    order_id, codename, epoch, dt, target["price"],
    order.side, order.takeprofit_price, order.stoploss_price, 
    target["trend"], rank, target["trade_pos_key"],
    target["tp_diff"], con["peak_broken_rate"], con["mado"], con["acc"],
    con["trend_rate"], con["chiko"],
    con["len_std"], con["hara_rate"], con["up_hige_rate"], con["dw_hige_rate"], con["len_avg"], 
    con["reversed_rate"], con["momiai1"], con["momiai2"],
    con["avg_dist_last"], con["avg_dist_min"], con["avg_dist_max"]
)
        try:
            self.maindb.execSql(sql)
        except Exception as e:
            print(e)

    
    
    def createOrders(self, epoch):
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

        def process_checkcode(codename, ticker):
            target = self.checkCode(codename, ep, unitsecs, ticker, config_path=env.config_path)
            return target

        def process_order(target):
            order, trade_pos_key = self.getOrder(ep, target, unitsecs)
            if order is not None:
                local_order_id = order.localId
                if self.analize_mode:
                    self.insertTradeInfo(local_order_id, codename, epoch, dt, codes.index(codename) + 1, target, order)
                    self.insertProba(local_order_id, target["probas"])
                return order, trade_pos_key
            return None, None

        i = 0
        targets = []
        while True:
            code_group = codes[i:i+MAX_THREADS]
            with ThreadPoolExecutor(max_workers=len(code_group)) as executor:
                futures = []
                for codename in code_group:
                    if codename in self.codetickers.keys():
                        ticker = self.codetickers[codename]
                    else:
                        ticker = Ticker({
                            "codename": codename,
                            "granularity": granularity,
                            "startep": epoch - unitsecs*self.period - self.size*unitsecs*2,
                            #"endep": epoch,
                            #"startep": self.ticker.startep - unitsecs*self.period - self.size*unitsecs*2,
                            "endep": self.ticker.endep,
                            "use_master": self.use_master
                        })
                        self.codetickers[codename] = ticker
                    
                    futures.append(executor.submit(process_checkcode, codename, ticker))

                for future in as_completed(futures):
                    target = future.result()
                    if target is not None:
                        targets.append(target)
            i += MAX_THREADS
            if i >= len(codes):
                break
        
        if len(targets) == 0:
            return []
        
        with ThreadPoolExecutor(max_workers=len(targets)) as executor:
            futures = []
            for target in targets:
                if self.tradePosExists(target["codename"], target["side"], target["trade_pos_key"]):
                    continue
                futures.append(executor.submit(process_order, target))
            
            for future in as_completed(futures):
                order, trade_pos_key = future.result()
                if order is not None:
                    self.updateTradePosCnt(order.codename, order.side, trade_pos_key)
                    orders.append(order)

        return orders


    def tradePosExists(self, codename, side, trade_pos_key):
        trade_poses = self.trade_poses.get(codename, {})
        if (side, trade_pos_key) in trade_poses.keys():
            return True
        return False


    def updateTradePosCnt(self, codename, side, trade_pos_key):
        trade_poses = self.trade_poses.get(codename, {})
        cnt = trade_poses.get((side, trade_pos_key), 0)
        cnt += 1
        trade_poses[(side, trade_pos_key)] = cnt
        self.trade_poses[codename] = trade_poses
        return cnt
    
    

    def checkTrade(self, epoch, order_id):
        order = self.orders[order_id]
        cnt = order["count"] + 1
        event = order["event"]
        if cnt >= self.epiration_limit:
            if order_id in self.orders.keys():
                del self.orders[order_id]
            return self.cancelTrade(epoch, event)

        # change take profit price 
        #if cnt >= self.epiration_middle:
        #    side = event.side
        #    price = event.trade_open_price
            
        #    order["count"] = cnt
        #    order["changed"] = True
        #    tp_diff = event.args["tp_diff"]
        #    tp = price + side*tp_diff/2
        #    return self.changeTrade(epoch, event, takeprofit_price=tp)
        
        order["count"] = cnt

    def onError(self, epoch, event):
        order = self.orders[event.id]
        order["changed"] = False


    def onTick(self, epoch):
        codenames = list(self.trade_poses.keys())
        for codename in codenames:
            trade_poses = self.trade_poses[codename]
            trade_pos_keys = list(trade_poses.keys())
            for k in trade_pos_keys:
                cnt = trade_poses[k]
                cnt += 1
                if cnt > self.trade_hold_cnt:
                    del trade_poses[k]
                else:
                    self.trade_poses[codename][k] = cnt

        orders = []
        for order_id in list(self.orders.keys()):
            order_inf = self.orders[order_id]
            if order_inf["event"].status != ESTATUS_TRADE_OPENED:
                continue
            
            event = self.checkTrade(epoch, order_id)
            if event is not None:
                orders.append(event)


        new_orders = self.createOrders(epoch)
        for order in new_orders:
            self.orders[order.id] = {
                "count": 0,
                "event": order,
                "changed": False
            }
        
        orders.extend(new_orders)
        return orders





if __name__ == "__main__":
    from time_ticker import TimeTicker
    from executor import Executor
    from trade_manager import TradeManager
    from portforio import Portoforio
    st = lib.str2epoch("2023-01-01T00:00:00")
    ed = lib.str2epoch("2024-01-01T00:00:00")
    os = lib.str2epoch("2024-01-01T00:00:00")
    
    '''
    sql = "SELECT distinct codename from bk_trades WHERE trade_name = 'anal_zigzag';"
    codes = []
    for (codename,) in PostgreSqlDB().execSql(sql):
        if codename in ["4385.T", "5253.T"]:
            continue
        codes.append(codename)
    '''
        
    #codes = ["1570.T"]
    codes = []

    args = {
        "codenames": codes,
        "use_master": True,
        "analize_mode": True,
        "n_targets": 100,
        "trade_name": "zzstrat_top3000vol2023",
        "ref_trade_name": "zzstrat_top3000vol",}
    strategy = ZigzagStrategy(args)
    ticker = TimeTicker("D", st, ed)
    executor = Executor()
    portforio = Portoforio("zzanal3", 1000000000, 1000000000)
    tm = TradeManager("Anal zigzag strategy", ticker, strategy, executor, portforio)
    report = tm.run(endep=ed, orderstopep=os)
        