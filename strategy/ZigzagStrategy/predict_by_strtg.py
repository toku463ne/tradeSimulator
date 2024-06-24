import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import MinMaxScaler
import numpy as np

import lib.naming as naming
from db.pgdf import PgDf


class StrtgPredictor:
    def __init__(self, use_master=False):
        self.use_master = use_master

    def feed(self, trade_name, startep, endep):
        db = PgDf(is_master=self.use_master)
        df = db.read_sql("""SELECT t.result, prefer_recent_peaks, peak_broken, mado, acc, trend_rate, 
chiko, len_std, hara_rate, up_hige_rate, dw_hige_rate, reversed_cnt/10, momiai
FROM zz_strtg_params AS z
JOIN trades as t on t.order_id = z.order_id
WHERE trade_name = '%s'
    and open_epoch >= %d and open_epoch <= %d;""" % (
        trade_name, startep, endep
    ))
        results = df['result'].map({'lose': -1, 'win': 1}).values.tolist()
        del df['result']
        
        #features = []
        #data = df.values.tolist()
        #scaler = MinMaxScaler()
        #for row in data:
        #    row = np.array(row)
        #    #row = scaler.fit_transform(row.reshape(-1, 1)).flatten()
        #    features.append(row)

        #X = pd.DataFrame(features)
        X = df
        y = pd.Series(results)

        


        classifiers = {
            "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
            "Logistic Regression": LogisticRegression(),
            "SVM": SVC(),
            "KNN": KNeighborsClassifier()
        }


        for name, clf in classifiers.items():
            scores = cross_val_score(clf, X, y, cv=5)
            print(f"{name}: {np.mean(scores):.2f} (+/- {np.std(scores):.2f})")

        """
        Random Forest: 0.51 (+/- 0.03)
        Logistic Regression: 0.56 (+/- 0.03)
        SVM: 0.55 (+/- 0.03)
        KNN: 0.53 (+/- 0.04)
        """


        #X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        #clf = RandomForestClassifier(n_estimators=100, random_state=42)
        #clf.fit(X_train, y_train)
        #y_pred = clf.predict(X_test)

        #accuracy = accuracy_score(y_test, y_pred)
        #print(f'Accuracy: {accuracy * 100:.2f}%')
