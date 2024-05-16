import sys, os
import falcon
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pyapi.index
import pyapi.chart
import pyapi.chartdefs


app = falcon.API()
app.add_route("/index", pyapi.index.Index())
app.add_route("/chart", pyapi.chart.Chart())
app.add_route("/chartdefs/{filename}", pyapi.chartdefs.ChartDef())
app.add_route("/chartdeflist", pyapi.chartdefs.ChartDefList())

application = app

