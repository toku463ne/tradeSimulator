from consts import *

class Executor(object):
    def OLDcancelOrder(self, epoch, orderEvent):
        (_, _, _, h, l, c, _) = orderEvent.getPrice(epoch)
        price = (h+l+c)/3
        if orderEvent.status == ESTATUS_ORDER_OPENED:
            orderEvent.closeOrder(epoch, "Order cancel")
        if orderEvent.status == ESTATUS_TRADE_OPENED:
            orderEvent.closeTrade(epoch, price, "Trade cancel")
        orderEvent.cmd = CMD_CANCEL
        return orderEvent
        


    def checkOrder(self, epoch, orderEvent):
        (_, _, _, h, l, _, _) = orderEvent.getPrice(epoch)
        price = orderEvent.price
        side = orderEvent.side
        tp = orderEvent.takeprofit_price
        sl = orderEvent.stoploss_price

        if side == SIDE_BUY:
            if tp > 0 and tp < price:
                orderEvent.setError(ERROR_BAD_ORDER, "Takeprofit is under order price under BUY action.")
                return False
            if sl > 0 and sl > price:
                orderEvent.setError(ERROR_BAD_ORDER, "Stoploss is over order price under BUY action.")
                return False
        
        if side == SIDE_SELL:
            if tp > 0 and tp > price:
                orderEvent.setError(ERROR_BAD_ORDER, "Takeprofit is over order price under SELL action.")
                return False
            if sl > 0 and sl < price:
                orderEvent.setError(ERROR_BAD_ORDER, "Stoploss is under order price under SELL action.")
                return False
        

        if orderEvent.cmd == CMD_CREATE_STOP_ORDER:
            if price > h or price < l:
                orderEvent.setError(ERROR_BAD_ORDER, "Wrong price in stop order.")
                return False
        return True


    # TODO: Issue error when the order is strange
    def detectOrderChange(self, epoch, orderEvent):
        (ep, dt, o, h, l, c, v) = orderEvent.getPrice(epoch)

        if ep < epoch:
            return

        side = orderEvent.side
        #price = (h+l+c)*1.0/3.0

        price = orderEvent.price
        expr = orderEvent.expiration
        order_expr = orderEvent.order_expiration

        if v == 0:
            return

        if orderEvent.status == ESTATUS_ORDER_OPENED:
            expired = False
            if order_expr > 0 and order_expr <= epoch:
                expired = True

            if orderEvent.cmd in [CMD_CREATE_LIMIT_ORDER, CMD_CREATE_MARKET_ORDER, CMD_CREATE_STOP_ORDER]:
                if expired:
                    orderEvent.closeOrder(epoch, "expired")
                    return orderEvent
        

            msg = ""

            if orderEvent.cmd == CMD_CREATE_MARKET_ORDER:
                orderEvent.openTrade(epoch, o, orderEvent.desc)
                return orderEvent
                
            elif orderEvent.cmd == CMD_CREATE_STOP_ORDER:
                if orderEvent.isValid(epoch) == False:
                    orderEvent.closeOrder(epoch, "expired before trade")
                    return orderEvent
                else:
                    if side == SIDE_BUY and orderEvent.price > l:
                        orderEvent.openTrade(epoch, price, orderEvent.desc)
                        return orderEvent
                    if side == SIDE_SELL and orderEvent.price < h:
                        orderEvent.openTrade(epoch, price, orderEvent.desc)
                        return orderEvent
                    
            elif orderEvent.cmd == CMD_CANCEL:
                orderEvent.closeOrder(epoch, "canceled")
                return orderEvent

            else:
                raise Exception("Non supported cmd")
            
        elif orderEvent.status == ESTATUS_TRADE_OPENED:
            tp = orderEvent.takeprofit_price
            sl = orderEvent.stoploss_price
            iswin = 0
            expired = False
            if expr > 0 and expr <= epoch:
                expired = True
            msg = ""
            canceled = False
            if orderEvent.cmd == CMD_CANCEL:
                canceled = True

            if expired or canceled:
                price = o
            
            if side == SIDE_BUY:
                if sl > 0 and l < sl:
                    iswin = -1
                    msg = "stoploss"
                    price = sl 
                elif tp > 0 and h > tp:
                    iswin = 1
                    msg = "takeprofit"
                    price = tp
                elif expired or canceled:
                    if orderEvent.trade_open_price < price:
                        iswin = 1
                    else:
                        iswin = -1
            elif side == SIDE_SELL:
                if sl > 0 and h > sl:
                    iswin = -1
                    msg = "stoploss"
                    price = sl 
                elif tp > 0 and l < tp:
                    iswin = 1
                    msg = "takeprofit"
                    price = tp
                elif expired or canceled:
                    if orderEvent.trade_open_price > price:
                        iswin = 1
                    else:
                        iswin = -1
                
            if expired:
                msg = "expired"
            if canceled:
                msg = "canceled"
            
            if iswin == 1 or iswin == -1:
                orderEvent.closeTrade(epoch, price, msg)
                return orderEvent
            if orderEvent.cmd == CMD_CHANGE_TRADE:
                return orderEvent
        elif orderEvent.status == ESTATUS_NONE:
            if orderEvent.cmd == CMD_CREATE_MARKET_ORDER or orderEvent.cmd == CMD_CREATE_STOP_ORDER:
                orderEvent.openTrade(epoch, price)
                return orderEvent

        return None

