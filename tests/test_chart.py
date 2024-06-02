import unittest
import json

import __init__
from pyapi.chart import Chart
from backtest.simpleMarketStrategy import run_simple_market

class TestChart(unittest.TestCase):
    def test_zigzag(self):
        params = {
        "codename": "^GSPC",
        "granularity": "D",
        "start_date": "2023-01-01",
        "end_date": "2024-01-01",
        "indicators": {
            "zigzag5": {
                "size": 5,
                "type": "zigzag"
            }
        },
        "trade_name": "test_simple_market_chart"
        }

        run_simple_market(params["trade_name"], 
                          params["codename"],
                          params["granularity"],
                          100,
                          params["start_date"] + "T00:00:00",
                          params["end_date"] + "T00:00:00")


        c = Chart()
        datastr = c.get_data(params)

        data = json.loads(datastr)
        values = data["indicators"]["zigzag5"]["values"]
        self.assertGreater(len(values["main"]), 0)
        self.assertGreater(len(values["middle"]), 0)

        btdatastr = c.get_backtest_data(params)
        btdata = json.loads(btdatastr)
        self.assertGreater(len(btdata), 0)
        first = btdata[list(btdata.keys())[0]]
        self.assertGreater(first["open"]["price"], 0)
        self.assertGreater(first["close"]["price"], 0)
        self.assertNotEqual(first["side"], 0)
        #print(btdata)


    def test_ichimoku(self):
        c = Chart()
        datastr = c.get_data({
            "codename": "^GSPC",
            "granularity": "D",
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
            "indicators": {
                "ichimoku": {
                    "type": "ichimoku"
                }
            }
        })

        data = json.loads(datastr)
        icvals = data["indicators"]["ichimoku"]["values"]
        self.assertGreater(len(icvals["tenkan"]), 0)
        self.assertGreater(len(icvals["kijun"]), 0)
        self.assertGreater(len(icvals["senkou1"]), 0)
        self.assertGreater(len(icvals["senkou2"]), 0)
        self.assertGreater(len(icvals["chikou"]), 0)


if __name__ == "__main__":
    unittest.main()
