from sklearn.cluster import KMeans
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import pandas as pd
import numpy as np
import joblib
import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
import lib
from db.pgdf import PgDf
from db.postgresql import PostgreSqlDB
from consts import *


class ZzCodePredictor:
    def __init__(self, trade_name, use_master=False):
        self.trade_name = trade_name
        self.datadir = lib.ensureDataDir(subdir=os.path.join("zigzagStrategy", trade_name))
        self.use_master = use_master
        self.db = PostgreSqlDB(is_master=False)
        self.db.createTable("zz_predicts")
        self.columns = ['side','peak_broken_rate','mado','acc','trend_rate',
                  'chiko','len_std','hara_rate','up_hige_rate',
                  'dw_hige_rate','reversed_rate','momiai1', 'momiai2', 
                  'avg_dist_last', 'avg_dist_max', 'avg_dist_min']
        

    def getPath(self, path_type, name):
        return os.path.join(self.datadir, "%s_%s.pkl" % (path_type, name))

    def getResultPath(self):
        return os.path.join(self.datadir, "result.json")
    
    def getKmeansGroupName(self, group_id):
        return "km_%05d" % group_id


    def getQuery(self, start, end, codenames=[]):
        code_cond = ""
        if len(codenames) > 0:
            code_cond = "AND t.codename in ('%s')" % "','".join(codenames)

        return """SELECT z.codename, z.dt, t.result, 
t.side, peak_broken_rate,mado,acc,
trend_rate,chiko,len_std,hara_rate,up_hige_rate,
dw_hige_rate,reversed_rate,momiai1,momiai2,
avg_dist_last, avg_dist_min, avg_dist_max
FROM
zz_strtg_params as z
JOIN trades as t on t.order_id = z.order_id
where
ep >= %d
AND ep <= %d
AND RIGHT(z.order_id, %d) = '%s'
%s""" % (
            start, end, len(self.trade_name), self.trade_name, code_cond
        )
    
    
    def km_classify(self, data, n_clusters=50):
        scaler = StandardScaler()
        X = data[self.columns]
        data_scaled = scaler.fit_transform(X)
        
        joblib.dump(scaler, self.getPath("scaler", "kmeans"))

        kmeans = KMeans(n_clusters=n_clusters, random_state=42)  # Adjust the number of clusters as needed
        clusters = kmeans.fit_predict(data_scaled)

        joblib.dump(kmeans, self.getPath("model", "kmeans"))

        data["clusters"] = clusters
        groups = list(set(clusters))
        km_groups = {}
        for group_id in groups:
            km_groups[group_id] = data[data.clusters == group_id][["result"] + self.columns]

        return km_groups

    
    def km_classify_new_data(self, side, cond_vals):
        # Load the saved scaler and K-Means model
        scaler = joblib.load(self.getPath("scaler", "kmeans"))
        kmeans = joblib.load(self.getPath("model", "kmeans"))

        c = cond_vals
        new_data = pd.DataFrame(
            {
                'side': [side],
                'peak_broken_rate': [c['peak_broken_rate']],
                'mado': [c['mado']],'acc': [c['acc']],'trend_rate': [c['trend_rate']],
                'chiko': [c['chiko']],'len_std': [c['len_std']],'hara_rate': [c['hara_rate']],'up_hige_rate': [c['up_hige_rate']],
                'dw_hige_rate': [c['dw_hige_rate']],'reversed_rate': [c['reversed_rate']],'momiai1': [c['momiai1']], 'momiai2': [c['momiai2']], 
                'avg_dist_last': [c['avg_dist_last']], 'avg_dist_max': [c['avg_dist_max']], 'avg_dist_min': [c['avg_dist_min']]
            }
        )

        
        # Handle missing values in new data
        new_data = new_data.fillna(new_data.mean())

        # Standardize the new data
        new_data_scaled = scaler.transform(new_data)

        # Predict the cluster for the new data
        new_clusters = kmeans.predict(new_data_scaled)

        return new_clusters[0]


    def train_groups(self, feed_startep, feed_endep, min_samples=10, threshold=0.7, n_clusters=50):
        self.feed_startep = feed_startep
        self.feed_endep = feed_endep
        self.min_samples = min_samples
        pg = PgDf(is_master=self.use_master)
        data = pg.read_sql(self.getQuery(self.feed_startep, self.feed_endep))
        groups = self.km_classify(data, n_clusters=n_clusters)
        for group_id, df in groups.items():
            self._train(self.getKmeansGroupName(group_id), df, threshold)


    def train_kobetsu(self, feed_startep, feed_endep, min_samples=10, 
              threshold=0.7):
        self.feed_startep = feed_startep
        self.feed_endep = feed_endep
        self.min_samples = min_samples
        pg = PgDf(is_master=self.use_master)
    
        sql = """SELECT DISTINCT codename FROM trades WHERE trade_name = '%s';""" % (self.trade_name)
        for (codename,) in self.db.execSql(sql):
            data = pg.read_sql(self.getQuery(feed_startep, feed_endep, [codename]))
            self._train(codename, data, threshold)


    def train_all(self, feed_startep, feed_endep, min_samples=10, 
              threshold=0.7):
        self.feed_startep = feed_startep
        self.feed_endep = feed_endep
        self.min_samples = min_samples
        pg = PgDf(is_master=self.use_master)
        data = pg.read_sql(self.getQuery(self.feed_startep, self.feed_endep))
        
        self._train("all", data, threshold)



    def _train(self, name, data, threshold=0.7):
        #pg = PgDf(is_master=self.use_master)
        #data = pg.read_sql(self.getQuery(self.feed_startep, self.feed_endep, codenames))

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
        X = data[self.columns]
        y = data.apply(calculate_dest, axis=1)
        
        samples = len(X)
        if samples < self.min_samples:
            return

        # Split the data into training and testing sets
        #X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        
        up_samples = len(y[y == 1])
        down_samples = len(y[y == 0])

        X = data[self.columns]
        y = data.apply(calculate_dest, axis=1)
        
        if len(X) < self.min_samples:
            return

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        model = XGBClassifier(random_state=42)
        model.fit(X_scaled, y)
        

        joblib.dump(model, self.getPath("model", name))
        joblib.dump(scaler, self.getPath("scaler", name))

        X_test_scaled = scaler.transform(X)
        proba = model.predict_proba(X_test_scaled)
        
        high_conf_predictions = []
        high_conf_actuals = []
        high_count_above_threshold = 0
        high_accuracy = 0
        low_conf_predictions = []
        low_conf_actuals = []
        low_count_above_threshold = 0
        low_accuracy = 0
        


        for i in range(len(proba)):
            if proba[i][1] >= threshold:
                high_conf_predictions.append(1)
                high_conf_actuals.append(y.iloc[i])
                high_count_above_threshold += 1
            
            if proba[i][0] >= threshold:
                low_conf_predictions.append(0)
                low_conf_actuals.append(y.iloc[i])
                low_count_above_threshold += 1
            

        
        # Calculate metrics for high confidence predictions
        if len(high_conf_predictions) > 0:
            high_accuracy = accuracy_score(high_conf_actuals, high_conf_predictions)

        if len(low_conf_predictions) > 0:
            low_accuracy = accuracy_score(low_conf_actuals, low_conf_predictions)
    

        #with open(self.getResultPath(), "w") as f:
        #    json.dump(result, f, indent=4)

        startep = self.feed_startep
        endep = self.feed_endep
        startdt = lib.epoch2str(self.feed_startep)
        enddt = lib.epoch2str(self.feed_endep)
        sql = """DELETE FROM zz_predicts WHERE trade_name = '%s' AND name = '%s' AND startep = %d AND endep = %d;
INSERT INTO zz_predicts(trade_name, name, startep, endep, startdt, enddt,
samples, n_ups, n_downs, 
threshold, high_accuracy, high_count_above_threshold, low_accuracy, low_count_above_threshold)
VALUES('%s', '%s', %d, %d, '%s', '%s', 
%d, %d, %d,
%f, %f, %d, %f, %d)
""" % (self.trade_name, name, startep, endep,
self.trade_name, name, startep, endep, startdt, enddt,
samples, up_samples, down_samples,
threshold, high_accuracy, high_count_above_threshold, low_accuracy, low_count_above_threshold
)
        self.db.execSql(sql)


    def predict_trade(self, codename, side, cond_vals):
        def _getModel(name):
            try:
                model = joblib.load(self.getPath("model", name))
                scaler = joblib.load(self.getPath("scaler", name))
                return model, scaler
            except:
                return None, None
        
        proba_all = 0
        proba_kobetsu = 0
        proba_group = 0

        (model, scaler) = _getModel("all")
        if model != None and scaler != None:
            proba_all = self._predict_trade(side, cond_vals, model, scaler)

        (model, scaler) = _getModel(codename)
        if model != None and scaler != None:
            proba_kobetsu = self._predict_trade(side, cond_vals, model, scaler)
        
        group_id = self.km_classify_new_data(side, cond_vals)
        (model, scaler) = _getModel(self.getKmeansGroupName(group_id))
        if model != None and scaler != None:
            proba_group = self._predict_trade(side, cond_vals, model, scaler)

        return {
            "all": proba_all,
            "kobetsu": proba_kobetsu,
            "group": proba_group
        }



    def _predict_trade(self, side, cond_vals, model, scaler):
        c = cond_vals
        input_data = scaler.transform(pd.DataFrame(
            {
                'side': [side],
                'peak_broken_rate': [c['peak_broken_rate']],
                'mado': [c['mado']],'acc': [c['acc']],'trend_rate': [c['trend_rate']],
                'chiko': [c['chiko']],'len_std': [c['len_std']],'hara_rate': [c['hara_rate']],'up_hige_rate': [c['up_hige_rate']],
                'dw_hige_rate': [c['dw_hige_rate']],'reversed_rate': [c['reversed_rate']],'momiai1': [c['momiai1']], 'momiai2': [c['momiai2']], 
                'avg_dist_last': [c['avg_dist_last']], 'avg_dist_max': [c['avg_dist_max']], 'avg_dist_min': [c['avg_dist_min']]
            }
        ))

        i = 0
        if side == SIDE_BUY:
            i = 1
        proba = float(model.predict_proba(input_data)[0][i])
        return proba




if __name__ == "__main__":
    from datetime import datetime
    import lib


    trade_name = 'zzstrat_top3000vol2'
    start = lib.dt2epoch(datetime(2016, 1, 1))
    end = lib.dt2epoch(datetime(2023, 1, 1))

    z = ZzCodePredictor(trade_name)
    z.train_groups(start, end, threshold=0.7, n_clusters=10)
    z.train_all(start, end, threshold=0.7)
    z.train_kobetsu(start, end, threshold=0.7)

    #df = z.inspect("3092.T", start, end)
    #df
