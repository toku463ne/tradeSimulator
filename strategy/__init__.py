from event.order import OrderEvent
from consts import *
trade_mode = TRADE_MODE_ONLY_BUY
import lib

class Strategy(object):    

    def preProcess(self, timeTicker, portforio):
        self.timeTicker = timeTicker
        self.portforio = portforio

    #def initAttrFromArgs(self, args, name, default=None):
    #    if name in args.keys():
    #        setattr(self, name, args[name])
    #    elif default is None:
    #        raise Exception("%s is necessary!" % name)
    #    else:
    #        setattr(self, name, default)
            
    # return list of order_events
    def onTick(self, epoch):
        pass
    
    # return void
    def onSignal(self, epoch, event):
        pass

    def onError(self, epoch, event):
        print("[error]%s: %s code=%s desc=%s" % (str(event.localId), lib.epoch2str(epoch, "%Y%m%d"), 
                event.codename, event.error_msg))
        pass

    def createMarketOrder(self, epoch, ticker, side, units, name="",
                        validep=0, takeprofit=0, stoploss=0, expiration=0, order_expiration=0,
                         desc="Market Order", args={}):
        #(_, _, price, _, _, _, _) = data_getter.getPrice(epoch)
        order = OrderEvent(CMD_CREATE_MARKET_ORDER, ticker, 
                          epoch=epoch, side=side,
                          units=units, name=name, validep=validep, 
                          takeprofit=takeprofit, stoploss=stoploss, 
                          expiration=expiration, order_expiration=order_expiration,
                          desc=desc, args=args)
        #order.openTrade(epoch, price, desc)
        return order
    
    def createStopOrder(self, epoch, ticker, side, units, price, name="",
                        validep=0, takeprofit=0, stoploss=0, expiration=0, order_expiration=0,
                        desc="Stop Order", args={}):
        #(_, _, price, _, _, _, _) = data_getter.getPrice(epoch+data_getter.unitsecs)
        order = OrderEvent(CMD_CREATE_STOP_ORDER, ticker, 
                          epoch=epoch, side=side, price=price,
                          units=units, name=name, validep=validep, 
                          takeprofit=takeprofit, stoploss=stoploss, 
                          expiration=expiration, order_expiration=order_expiration,
                          desc=desc, args=args)
        #order.openTrade(epoch, price, desc)
        return order
        
    def cancelOrder(self, epoch, _id):
        return OrderEvent(CMD_CANCEL, epoch=epoch, _id=_id)
          
    def cancelTrade(self, epoch, event):
        #return OrderEvent(CMD_CANCEL, ticker, epoch=epoch, _id=_id)
        event.epoch = epoch
        event.cmd = CMD_CANCEL
        return event
    
    def changeTrade(self, epoch, event, takeprofit_price=0, stoploss_price=0):
        if takeprofit_price > 0:
            event.takeprofit_price = takeprofit_price
        if stoploss_price > 0:
            event.stoploss_price = stoploss_price
        
        if takeprofit_price > 0 or stoploss_price > 0:
            event.last_change_epoch = epoch

        event.cmd = CMD_CHANGE_TRADE
        return event
          
    def getPlotElements(self, color="k"):
        return []


    def initAttrFromConfig(self, args, name, default=None):
        if name in args.keys():
            setattr(self, name, args[name])
        elif default is None:
            raise Exception("%s is necessary!" % name)
        else:
            setattr(self, name, default)