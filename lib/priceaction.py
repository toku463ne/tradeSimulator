import numpy as np


# Check if the prices are in momiai form
def checkMomiai(cl, trend_rate=0.7):
    u_cnt = 0
    d_cnt = 0
    le = len(cl)
    for i in range(1, le):
        if cl[i] - cl[i-1] > 0:
            u_cnt += 1
        elif cl[i] - cl[i-1] < 0:
            d_cnt += 1
    
    le = le - 1
    if u_cnt/le < trend_rate and d_cnt/le < trend_rate:
        return True
    
    u_cnt = 0
    d_cnt = 0
    le = len(cl)
    for i in range(2, le):
        if cl[i] - cl[i-2] > 0:
            u_cnt += 1
        elif cl[i] - cl[i-2] < 0:
            d_cnt += 1
    
    le = le - 2
    if u_cnt/le < trend_rate and d_cnt/le < trend_rate:
        return True
    
    return False
    

def checkMado(ol, hl, ll, window_len_rate=0.001):
    mado = False
    if ll[-1] - hl[-2] > ol[-1]*window_len_rate:
        mado = True
    elif ll[-2] - hl[-1] > ol[-1]*window_len_rate:
        mado = True

    return mado

# Check std rate of the last cancle length
# Check if there is window between the last and the one before last candle
def checkLastCandle(ol, hl, ll, cl):
    ol = np.array(ol)
    hl = np.array(hl)
    ll = np.array(ll)
    cl = np.array(cl)
    
    le = abs(ol - cl)
    a = le.mean()
    s = le.std()
    len_std = (le[-1] - a)/s

    o = ol[-1]
    h = hl[-1]
    l = ll[-1]
    c = cl[-1]

    last_len = h - l
    hara_rate = (c - o)/last_len

    up_hige_rate = (h-max(c, o))/last_len
    dw_hige_rate = (min(c, o)-l)/last_len

    return {
        "len_std": len_std,
        "hara_rate": hara_rate,
        "up_hige_rate": up_hige_rate,
        "dw_hige_rate": dw_hige_rate,
        "len_avg": a
    }


def checkChiko(cl, chiko_span=26):
    period = len(cl) - chiko_span
    u_cnt = 0
    d_cnt = 0
    for i in range(period):
        if cl[i] > cl[i+chiko_span]:
            d_cnt += 1
        elif cl[i] < cl[i+chiko_span]:
            u_cnt += 1
    
    return d_cnt/period, u_cnt/period
