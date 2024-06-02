import numpy as np


# Check if the prices are in momiai form
def _checkTrendRate(cl):
    u_cnt = 0
    d_cnt = 0
    le = len(cl)
    for i in range(1, le):
        if cl[i] - cl[i-1] > 0:
            u_cnt += 1
        elif cl[i] - cl[i-1] < 0:
            d_cnt += 1
    
    le = le - 1
    ur = u_cnt/le
    dr = d_cnt/le
    trend_rate1 = max(ur, dr)
    if dr > ur:
        trend_rate1 *= -1
    
    u_cnt = 0
    d_cnt = 0
    le = len(cl)
    for i in range(2, le):
        if cl[i] - cl[i-2] > 0:
            u_cnt += 1
        elif cl[i] - cl[i-2] < 0:
            d_cnt += 1
    
    le = le - 2
    ur = u_cnt/le
    dr = d_cnt/le
    trend_rate2 = max(ur, dr)
    if dr > ur:
        trend_rate2 *= -1
    
    return (trend_rate1+trend_rate2)/2

    #return max(trend_rate1, trend_rate2)
    
def checkTrendRate(hl, ll, cl):
    hr = _checkTrendRate(hl)
    lr = _checkTrendRate(ll)
    cr = _checkTrendRate(cl)
    
    has_trend = False
    if (hr>0 and lr>0 and cr>0):
        has_trend = True
    if (hr<0 and lr<0 and cr<0):
        has_trend = True

    return (hr+lr+cr)/3, has_trend

def checkMado(ol, hl, ll):
    mado = max((ll[-1] - hl[-2])/ol[-1], (ll[-2] - hl[-1])/ol[-1])
    return float(mado)

# Check std rate of the last cancle length
# Check if there is window between the last and the one before last candle
def checkLastCandle(ol, hl, ll, cl):
    ol = np.array(ol)
    hl = np.array(hl)
    ll = np.array(ll)
    cl = np.array(cl)
    
    le = abs(ol - cl)
    a = np.nan_to_num(le.mean())
    s = np.nan_to_num(le.std())
    if s > 0:
        len_std = np.nan_to_num((le[-1] - a)/s)
    else:
        len_std = 0

    o = np.nan_to_num(ol[-1])
    h = np.nan_to_num(hl[-1])
    l = np.nan_to_num(ll[-1])
    c = np.nan_to_num(cl[-1])

    if o <= 0 or h <= 0 or l <= 0 or c <= 0:
        return
        
    last_len = h - l
    hara_rate = (c - o)/last_len

    up_hige_rate = (h-max(c, o))/last_len
    dw_hige_rate = (min(c, o)-l)/last_len

    return {
        "len_std": float(len_std),
        "hara_rate": float(hara_rate),
        "up_hige_rate": float(up_hige_rate),
        "dw_hige_rate": float(dw_hige_rate),
        "len_avg": float(a)
    }


def checkChiko(cl, chiko_span=26):
    period = len(cl) - chiko_span
    if period == 0:
        return (0, 0)
    u_cnt = 0
    d_cnt = 0
    for i in range(period):
        if cl[i] > cl[i+chiko_span]:
            d_cnt += 1
        elif cl[i] < cl[i+chiko_span]:
            u_cnt += 1
    
    return d_cnt/period, u_cnt/period
