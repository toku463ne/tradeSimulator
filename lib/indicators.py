import numpy as np
import math

def sma(p, span=20):
    v = np.array(p)
    x = np.convolve(v, np.ones(span), 'valid') / span
    date_start_index = span -1 
    return x.tolist(), date_start_index


def zigzag(eps, dt, h, l, v, size=5, middle_size=2, peak_num=0):
    peakidxs = []
    dirs = []

    def _updateZigZag(newdir, i, p):
        if abs(newdir) == 1 or len(dirs) == 0 or newdir*dirs[-1] <= -4:
            peakidxs.append(i)
            dirs.append(newdir)
            return
        if len(dirs) > 0:
            for j in range(1, len(dirs)+1):
                if newdir*dirs[-j] <= -4:
                    break

                jidx = peakidxs[-j]
                if abs(dirs[-j]) == 2:
                    if newdir > 0:
                        if p[i] > p[jidx]:
                            dirs[-j] = 1
                        else:
                            newdir = 1
                            break
                    else:
                        if p[i] < p[jidx]:
                            dirs[-j] = -1
                        else:
                            newdir = -1
                            break
            peakidxs.append(i)
            dirs.append(newdir)
    
    for i in range(len(eps)-size*2, 0, -1):
        midi = i + size
        midh = h[midi]
        midl = l[midi]
        
        #import lib
        #from datetime import datetime
        #if lib.epoch2dt(ep[midi]) == datetime(2022,1, 21):
        #    print("here")

        if midh == max(h[i:i+size*2]):
            _updateZigZag(2, midi, h)
        elif midl == min(l[i:i+size*2]):
            _updateZigZag(-2, midi, l)
        elif midh == max(h[i:i+size+middle_size+1]):
            _updateZigZag(1, midi, h)
        elif midl == min(l[i:i+size+middle_size+1]):
            _updateZigZag(-1, midi, l)
        
        if peak_num > 0 and len(peakidxs) >= peak_num:
            break

    date_start_index = size*2-1
    dirs.reverse()
    peakidxs.reverse()

    newep = []
    newdt = []
    newv = []
    prices = []
    dists = [0]
    oldidx = 0
    for i in range(len(peakidxs)):
        idx = peakidxs[i]
        d = dirs[i]
        if d > 0:
            prices.append(h[idx])
        if d < 0:
            prices.append(l[idx])
        vl = 0
        if i > 0:
            cnt = 0
            cnts = 0
            s = 0
            for j in range(peakidxs[i-1]+1, peakidxs[i]+1):
                s += (cnt+1)*v[j]
                cnts += cnt+1
                cnt += 1
            vl = s/cnts
        newep.append(eps[idx])
        newdt.append(dt[idx])
        newv.append(vl)
        if i > 0:
            dists.append(idx - oldidx)
        oldidx = idx
    
    return newep, newdt, dirs, prices, newv, dists, date_start_index


def ichimoku(h, l, c, tenkan_span=9, kijun_span=26, senkou1_span=26, senkou2_span=52, chikou_span=26):
    if len(c) < senkou2_span:
        raise Exception("Data size is too short")
    
    # Helper function to calculate moving averages and spans
    def calculate_span(period, high_data, low_data):
        return [np.max(high_data[i-period+1:i+1]) if i >= period-1 else None for i in range(len(high_data))],\
               [np.min(low_data[i-period+1:i+1]) if i >= period-1 else None for i in range(len(low_data))]
    
    # Calculate Tenkan-sen (Conversion Line)
    tenkan_sen_high, tenkan_sen_low = calculate_span(tenkan_span, h, l)
    tenkan_sen = [(high + low) / 2 if high is not None and low is not None else None for high, low in zip(tenkan_sen_high, tenkan_sen_low)]
    
    # Calculate Kijun-sen (Base Line)
    kijun_sen_high, kijun_sen_low = calculate_span(kijun_span, h, l)
    kijun_sen = [(high + low) / 2 if high is not None and low is not None else None for high, low in zip(kijun_sen_high, kijun_sen_low)]
    
    # Calculate Senkou Span A (Leading Span A)
    senkou1 = [(ts + ks) / 2 if ts is not None and ks is not None else None for ts, ks in zip(tenkan_sen, kijun_sen)]
    senkou1 = [None] * senkou1_span + senkou1[:-senkou1_span]   # Shifted forward
    
    # Calculate Senkou Span B (Leading Span B)
    senkou2_span_high, senkou2_span_low = calculate_span(senkou2_span, h, l)
    senkou2 = [(high + low) / 2 if high is not None and low is not None else None for high, low in zip(senkou2_span_high, senkou2_span_low)]
    senkou2_span_delay = int(senkou2_span / 2)
    senkou2 = [None] * senkou2_span_delay + senkou2[:-senkou2_span_delay]  # Shifted forward
    
    # Calculate Chikou Span (Lagging Span)
    chikou = c[chikou_span:] + [None] * chikou_span if len(c) > chikou_span else [None] * len(c)
    
    # Combine all spans into a single dictionary
    ichimoku_data = {
        "tenkan": tenkan_sen,
        "kijun": kijun_sen,
        "senkou1": senkou1,
        "senkou2": senkou2,
        "chikou": chikou
    }
    
    return ichimoku_data


def peaks(eps, dt, h, l, size=10):
    peaks = []
    for i in range(len(eps)-size*2):
        midi = i + size
        midh = h[midi]
        midl = l[midi]
        if midh == max(h[i:i+size*2]):
            peaks.append({"ep": eps[midi], "dt": dt[midi], "side": 1, "index": midi, "price": midh})
        elif midl == min(l[i:i+size*2]):
            peaks.append({"ep": eps[midi], "dt": dt[midi], "side": -1, "index": midi, "price": midl})
    return peaks