import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import os, json
import numpy as np

import __init__
import lib
from db.pgdf import PgDf
from consts import *

class ZzPredictor:
    def __init__(self, trade_name, feed_startep, feed_endep, use_master=False):
        self.trade_name = trade_name
        self.feed_startep = feed_startep
        self.feed_endep = feed_endep
        self.datadir = lib.ensureDataDir(subdir="zigzagStrategy")
        self.use_master = use_master
        

    def getPath(self, path_type):
        return os.path.join(self.datadir, "%s.pkl" % (path_type))

    def getResultPath(self):
        return os.path.join(self.datadir, "result.json")


    def getQuery(self, start, end, additional_cond=""):
        return """SELECT z.codename, z.dt, t.result, 
t.side, peak_broken_rate,mado,acc,
trend_rate,chiko,len_std,hara_rate,up_hige_rate,
dw_hige_rate,reversed_rate,momiai1,momiai2,
avg_dist_last, avg_dist_min, avg_dist_max
FROM
zz_strtg_params as z
JOIN trades as t on t.order_id = z.order_id
where
AND ep >= %d
AND ep <= %d
AND RIGHT(z.order_id, %d) = '%s'
AND %s""" % (
            start, end, len(self.trade_name), self.trade_name, additional_cond
        )


    def train(self, high_threshold=0.6, low_threshold=0.4):
        pg = PgDf(is_master=self.use_master)
        data = pg.read_sql(self.getQuery(self.feed_startep, self.feed_endep))

        def calculate_dest(row):
            if row['side'] == 1 and row['result'] == 'win':
                return 1
            elif row['side'] == 1 and row['result'] == 'lose':
                return 0
            elif row['side'] == -1 and row['result'] == 'win':
                return 0
            elif row['side'] == -1 and row['result'] == 'lose':
                return 1
            else:
                return 0.5  # or some default value if needed

        ## Preprocess the data
        #data['result'] = data['result'].map({'win': 1, 'lose': 0})

        # Features and target
        X = data[['side','peak_broken_rate','mado','acc','trend_rate',
                  'chiko','len_std','hara_rate','up_hige_rate',
                  'dw_hige_rate','reversed_rate','momiai1', 'momiai2', 
                  'avg_dist_last', 'avg_dist_max', 'avg_dist_min']]
        y = data.apply(calculate_dest, axis=1)
        

        # Split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Standardize the features
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)

        # Train a Random Forest classifier
        clf = RandomForestClassifier(random_state=42)
        clf.fit(X_train, y_train)

        # Save the trained model and the scaler
        joblib.dump(clf, self.getPath("model"))
        joblib.dump(scaler, self.getPath("scaler"))

        self.evaluate_model_with_threshold_count(X_test, y_test, 
                    high_threshold=high_threshold, low_threshold=low_threshold)


    def predict_trades(self, start, end):
        model = joblib.load(self.getPath("model"))
        scaler = joblib.load(self.getPath("scaler"))
        pg = PgDf(is_master=self.use_master)
        data = pg.read_sql(self.getQuery(start, end))

        input_data = data[['side','peak_broken_rate','mado','acc','trend_rate',
                  'chiko','len_std','hara_rate','up_hige_rate',
                  'dw_hige_rate','reversed_rate','momiai1', 'momiai2', 
                  'avg_dist_last', 'avg_dist_max', 'avg_dist_min']]
        
        # Standardize the input features
        input_data = scaler.transform(input_data)
        
        # Predict probabilities
        proba = model.predict_proba(input_data).T

        #return pd.DataFrame({
        #    'codename': data['codename'],
        #    'dt': data['dt'],
        #    'side': data['side'],
        #    'proba0': proba[0],
        #    'proba1': proba[1],
        #    'result': data['result'].map({'win': 1, 'lose': -1})
        #})

        return pd.DataFrame({
            'codename': data['codename'],
            'dt': data['dt'],
            'predicted': np.where(proba[0] > 0.6, 1, np.where(proba[0] < 0.4, -1, 0)),
            'proba': proba[0],
            'result': data['result'].map({'win': 1, 'lose': -1})
        })

    
    
        
    def evaluate_model_with_threshold_count(self, X_test, y_test, high_threshold=0.6, low_threshold=0.4):
        model = joblib.load(self.getPath("model"))
        scaler = joblib.load(self.getPath("scaler"))
        
        # Standardize the test data
        X_test = pd.DataFrame(X_test, columns=scaler.feature_names_in_)
        X_test_scaled = scaler.transform(X_test)
        
        # Predict probabilities
        proba = model.predict_proba(X_test_scaled)
        
        high_conf_predictions = []
        high_conf_actuals = []
        low_conf_predictions = []
        low_conf_actuals = []
        count_above_high_threshold = 0
        count_below_low_threshold = 0
        
        for i in range(len(proba)):
            if proba[i][1] >= high_threshold or proba[i][0] >= high_threshold:
                count_above_high_threshold += 1
                if proba[i][1] >= high_threshold:
                    high_conf_predictions.append(1)
                    high_conf_actuals.append(y_test.iloc[i])
                elif proba[i][0] >= high_threshold:
                    high_conf_predictions.append(0)
                    high_conf_actuals.append(y_test.iloc[i])
            if proba[i][1] <= low_threshold or proba[i][0] <= low_threshold:
                count_below_low_threshold += 1
                if proba[i][1] <= low_threshold:
                    low_conf_predictions.append(1)
                    low_conf_actuals.append(y_test.iloc[i])
                elif proba[i][0] <= low_threshold:
                    low_conf_predictions.append(0)
                    low_conf_actuals.append(y_test.iloc[i])

        result = {}
        
        # Calculate metrics for high confidence predictions
        if len(high_conf_predictions) > 0:
            accuracy_high = accuracy_score(high_conf_actuals, high_conf_predictions)
            precision_high = precision_score(high_conf_actuals, high_conf_predictions,average='micro')
            recall_high = recall_score(high_conf_actuals, high_conf_predictions,average='micro')
            f1_high = f1_score(high_conf_actuals, high_conf_predictions,average='micro')
            
            result["high_threshold"] = high_threshold
            result["accuracy_high"] = accuracy_high
            result["precision_high"] = precision_high
            result["recall_high"] = recall_high
            result["f1_high"] = f1_high
            result["count_above_high_threshold"] = count_above_high_threshold
        else:
            result["high_threshold"] = high_threshold
            result["count_above_high_threshold"] = count_above_high_threshold

        # Calculate metrics for low confidence predictions
        if len(low_conf_predictions) > 0:
            accuracy_low = accuracy_score(low_conf_actuals, low_conf_predictions)
            precision_low = precision_score(low_conf_actuals, low_conf_predictions,average='micro')
            recall_low = recall_score(low_conf_actuals, low_conf_predictions,average='micro')
            f1_low = f1_score(low_conf_actuals, low_conf_predictions,average='micro')
            
            result["low_threshold"] = low_threshold
            result["accuracy_low"] = accuracy_low
            result["precision_low"] = precision_low
            result["recall_low"] = recall_low
            result["f1_low"] = f1_low
            result["count_below_low_threshold"] = count_below_low_threshold

        else:
            result["low_threshold"] = low_threshold
            result["count_below_low_threshold"] = count_below_low_threshold

        with open(self.getResultPath(), "w") as f:
            json.dump(result, f, indent=4)

    
    def printResult(self):
        result_path = self.getResultPath()
        if os.path.exists(result_path):
            with open(result_path, "r") as f:
                print(json.load(f))
        else:
            print("{}")


if __name__ == "__main__":
    from datetime import datetime

    from analyze.zigzagStrategy.bk.predictor import ZzPredictor
    import lib

    trade_name = 'zzstrat_top1000vol_bothside3'
    start = lib.dt2epoch(datetime(2018, 1, 1))
    end = lib.dt2epoch(datetime(2023, 1, 1))

    z = ZzPredictor(trade_name, start, end)
    z.train(high_threshold=0.6, low_threshold=0.4)
    z.printResult()
