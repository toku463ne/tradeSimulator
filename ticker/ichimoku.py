from ticker import Ticker
import lib.indicators as libind


class Ichimoku(Ticker):
    def __init__(self, config):
        super(Ichimoku, self).__init__(config)
        #tenkan_span=9, kijun_span=26, senkou1_span=26, senkou2_span=52, chikou_span=26
        self.tenkan_span = config.get("tenkan_span", 9)
        self.kijun_span = config.get("kijun_span", 26)
        self.senkou1_span = config.get("senkou1_span", 26)
        self.senkou2_span = config.get("senkou2_span", 52)
        self.chikou_span = config.get("chikou_span", 26)

        #self.initData()

    def initData(self, ohlcv=[]):
        super(Ichimoku, self).initData(ohlcv)
        self.ichimoku = libind.ichimoku(self.h, self.l, self.c,
            self.tenkan_span, self.kijun_span, self.senkou1_span, self.senkou2_span, self.chikou_span)
        
        
    def getData(self, i, n=0):
        '''
        ichimoku_data = {
            "tenkan": tenkan_sen,
            "kijun": kijun_sen,
            "senkou1": senkou_span_a,
            "senkou2": senkou_span_b,
            "chikou": chikou_span
        }
        '''
        ic = self.ichimoku
        if n == 1 and i >= 0:
            return (self.eps[i], self.dt[i], 
                    ic["tenkan"][i],ic["kijun"][i],
                    ic["senkou1"][i],ic["senkou2"][i],
                    ic["chikou"][i])
        elif i >= 0:
            j = i-n+1
            i = i+1
            return (self.eps[j:i], self.dt[j:i],
                    ic["tenkan"][j:i],ic["kijun"][j:i],
                    ic["senkou1"][j:i],ic["senkou2"][j:i],
                    ic["chikou"][j:i])
        else:
            return (0,None, None, None, None, None, None)