import __init__
import unittest
from pyapi.chart import Chart
import lib
import json

class TestDataGetterApi(unittest.TestCase):
    def get_day(self, epstr):
        return lib.epoch2dt(int(epstr)/1000).day

    def test_get_data(self):
        chart = Chart()
        
        start = "2021-11-01T00:00:00"
        end = "2021-11-30T00:00:00"
        datetime_format = '%Y-%m-%dT%H:%M:%S'

        data = chart.get_data({
            "codename": "^N225", 
            "granularity": "D", 
            "start_date": start, 
            "end_date": end, 
            "waitDownload": False, 
            "datetime_format": datetime_format
            }
        )
        data = json.loads(data)["ohlcv"]

        self.assertEqual(self.get_day(data[0]["Date"]), 1)
        self.assertEqual(self.get_day(data[-1]["Date"]), 30)
        
    def test_sma(self):
        chart = Chart()
        
        start = "2021-11-01T00:00:00"
        end = "2021-11-30T00:00:00"
        datetime_format = '%Y-%m-%dT%H:%M:%S'

        data = chart.get_data({
            "codename": "^N225", 
            "granularity": "D", 
            "start_date": start, 
            "end_date": end, 
            "waitDownload": False, 
            "datetime_format": datetime_format,
            "indicators": {
                "sma20": {
                    "span": 5,
                    "type": "sma"
                }
            }
        })
        values = json.loads(data)["indicators"]["sma20"]["values"]

        self.assertEqual(self.get_day(values[0]["Date"]), 8)
        self.assertEqual(self.get_day(values[-1]["Date"]), 30)

    def test_zigzag(self):
        chart = Chart()
        
        start = "2021-11-01T00:00:00"
        end = "2021-11-30T00:00:00"
        datetime_format = '%Y-%m-%dT%H:%M:%S'

        data = chart.get_data({
            "codename": "^N225", 
            "granularity": "D", 
            "start_date": start, 
            "end_date": end, 
            "waitDownload": False, 
            "datetime_format": datetime_format,
            "indicators": {
                "zigzag": {
                    "size": 5,
                    "type": "zigzag"
                }
            }
        })
        values = json.loads(data)["indicators"]["zigzag"]["values"]["main"]

        self.assertEqual(self.get_day(values[0]["Date"]), 11)
        self.assertEqual(self.get_day(values[-1]["Date"]), 16)
        

if __name__ == "__main__":
    unittest.main()
