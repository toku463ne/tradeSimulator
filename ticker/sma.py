from ticker import Ticker
import lib.indicators as libind


class SMA(Ticker):
    def __init__(self, config):
        super(SMA, self).__init__(config)
        self.span = config.get("span", 5)

        #self.initData()

    def initData(self, ohlcv=[]):
        super(SMA, self).initData(ohlcv)
        p = self.c
        x, start_i = libind.sma(p, self.span)
        self.p = x
        self.eps = self.eps[start_i:]
        self.dt = self.dt[start_i:]
        
        
    def getData(self, i, n=0):
        if n == 1 and i >= 0:
            return (self.eps[i], self.dt[i], self.p[i])
        elif i >= 0:
            j = i-n+1
            i = i+1
            return (self.eps[j:i], self.dt[j:i], self.p[j:i])
        else:
            return (0,None, 0)