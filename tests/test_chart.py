import unittest
import __init__
from pyapi.chart import Chart
import json

class TestChart(unittest.TestCase):
    def test_zigzag(self):
        c = Chart()
        datastr = c.get_data({
        "codename": "^GSPC",
        "granularity": "D",
        "start_date": "2023-01-01",
        "end_date": "2024-01-01",
        "indicators": {
            "zigzag5": {
                "size": 5,
                "type": "zigzag"
            }
            }
        })

        data = json.loads(datastr)
        values = data["indicators"]["zigzag5"]["values"]
        self.assertGreater(len(values["main"]), 0)
        self.assertGreater(len(values["middle"]), 0)


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
