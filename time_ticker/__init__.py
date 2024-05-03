import lib.tradelib as tradelib

class TimeTicker(object):
    def __init__(self, granularity, startep, endep):
        self.granularity = granularity
        self.interval = tradelib.getUnitSecs(granularity)
        self.startep = startep
        self.endep = endep
        self.epoch = startep
        self.EOF = False

    def tick(self):
        self.epoch += self.interval
        if self.epoch > self.endep:
            self.EOF = True
            return False
        else:
            return True
