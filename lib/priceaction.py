import numpy as np


import lib.indicators as ind


# Check if the prices are in momiai form
def _checkTrendRate(cl):
    u_cnt = 0
    d_cnt = 0
    s = 0
    
    s_cnt = len(cl)-2
    for j in range(s_cnt):
        u_cnt = 0
        d_cnt = 0
        k = j+1
        for i in range(k, len(cl)):
            if cl[i] - cl[i-k] > 0:
                u_cnt += 1
            elif cl[i] - cl[i-k] < 0:
                d_cnt += 1

        le = len(cl) - j - 1
        ur = u_cnt/le
        dr = d_cnt/le
        trend_rate = max(ur, dr)
        if dr > ur:
            trend_rate *= -1
    
        s += trend_rate
    
    return s/s_cnt

    
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

def checkAccumulation(ol, cl):
    ol = np.array(ol)
    cl = np.array(cl)
    r = _checkTrendRate(cl-ol)
    r = np.nan_to_num(r)
    return r

def _checkMomiai(hl, ll):
    h = hl[-1]
    l = ll[-1]
    total = len(hl)
    cnt = 0
    for i in range(total):
        if (l >= ll[i] and l <= hl[i]) or (h >= ll[i] and h <= hl[i]):
            cnt += 1
    
    return cnt*1.0/total

def checkMomiai(hl, ll, n_targets=2):
    s = 0
    for i in range(n_targets):
        starti = n_targets -i -1
        endi = i+1
        s += _checkMomiai(hl[starti:-endi], ll[starti:-endi])

    return s/n_targets



def checkMado(ol, hl, ll, cl):
    if ol[-1] > cl[-2] and ll[-1] < hl[-2]:
        return 0.0
    if ol[-1] < cl[-2] and hl[-1] > ll[-2]:
        return 0.0

    le = max(abs(ol[-1]-cl[-1]), abs(ol[-2]-cl[-2]))
    if le == 0:
        return 0.0
    mado = abs((cl[-2] - ol[-1])/le)
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
        
    leg_len = float(max(hl) - min(ll))
    if leg_len == 0:
        return

    hara_rate = float((c - o)/leg_len)

    up_hige_rate = (h-max(c, o))/leg_len
    dw_hige_rate = (min(c, o)-l)/leg_len

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

def distFromAvg(prices):
    prices = np.array(prices)
    mean = prices.mean()
    std = prices.std()
    dists = (prices - mean) / std
    return dists[-1], min(dists), max(dists)

