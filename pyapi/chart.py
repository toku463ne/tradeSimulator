import sys, os, logging
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import env
import lib
import data_getter
import json
import pyapi.chart_ele as ele

class Chart(object):
    def adjust_data(self, data):
        start = data["start_date"]
        end = data["end_date"]
        if len(start) == 10:
            start = start + "T00:00:00"
            end = end + "T00:00:00"
        data["start_date"] = start
        data["end_date"] = end
        return data


    def get_data(self,data):
        data = self.adjust_data(data) 
        codename = data["codename"]
        granularity = data["granularity"]
        start = data["start_date"]
        end = data["end_date"]

        logging.info("Get data with codename=%s granularity=%s" % (codename, granularity))
        
        dg = data_getter.getDataGetter(codename, granularity)
        (eps, dt, o, h, l, c, v) = dg.getPrices(lib.str2epoch(start), lib.str2epoch(end))
        
        ohlcv = []
        for i in range(len(eps)):
            item = {}
            item["Date"] = eps[i]*1000
            item["Close"] = c[i]
            item["Open"] = o[i]
            item["Low"] = l[i]
            item["High"] = h[i]
            item["Volume"] = v[i]
            ohlcv.append(item)
        
        data["ohlcv"] = ohlcv
        
        if not "indicators" in data.keys():
            return json.dumps(data).replace("\r", "").replace("\n", "")

        for indicator_name in data["indicators"].keys():
            indicator = data["indicators"][indicator_name]
            ind_type = indicator["type"]
            chart_type = "line"
            if ind_type == "sma":
                values = ele.get_sma_chart_values(indicator_name, eps, c, int(indicator["span"]))
            if ind_type == "zigzag":
                chart_type = "zigzag"
                values = ele.get_zigzag_chart_values(indicator_name, eps, 
                    dt, h, l, v, int(indicator["size"]))
            if ind_type == "ichimoku":
                chart_type = "ichimoku"
                values = ele.get_ichimoku_chart_values(indicator_name, eps, h, l, c)

            indicator["chart_type"] = chart_type
            indicator["values"] = values

            data["indicators"][indicator_name] = indicator

        return json.dumps(data).replace("\r", "").replace("\n", "")

    def get_backtest_data(self, data):
        if "trade_name" not in data.keys():
            return '{}'

        data = self.adjust_data(data)
            
        tradename = data["trade_name"]
        codename = data["codename"]
        startep = lib.str2epoch(data["start_date"])
        endep = lib.str2epoch(data["end_date"])

        data = ele.get_backtest_chart_values(tradename, codename, startep, endep)
        return json.dumps(data).replace("\r", "").replace("\n", "")



    def on_post(self, req, resp, **kwargs):
        try:
            args = req.media
            chartparams = json.loads(args["chartparams"])
            print(chartparams)
            data = self.get_data(chartparams)
            backtest_data = self.get_backtest_data(chartparams)
            
            html = ""
            with open("%s/pyapi/templates/am_ohlcv.html" % env.BASE_DIR, "r") as f:
                html = f.read()
            #with open("%s/charts/samples/candlechart.html" % env.BASE_DIR, "r") as f:
            #    html = f.read()

            resp.content_type = 'text/html'
            html = html.replace("#AM_OHLCV_DATA#", data)
            html = html.replace("#AM_OHLCV_INSTRUMENT#", chartparams["codename"])
            html = html.replace("#AM_OHLCV_BACKTESTDATA#", backtest_data)
            resp.text = html
        except Exception as e:
            resp.content_type = 'text/html'
            resp.text = e
            logging.error(e)
