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


class OhlcvPredictor:
    def __init__(self, granularity="D", n_candles=5, use_master=False):
        self.n_candles = n_candles
        self.tablename = naming.ohlcvTable(granularity)
        self.use_master = use_master

    def feed(self, trade_name, startep, endep):
        tablename = self.tablename
        n_candles = self.n_candles

        db = PgDf(is_master=self.use_master)
        trades_df = db.read_sql("""select codename, open_epoch, result 
    from trades
    where trade_name = '%s'
    and open_epoch >= %d and open_epoch <= %d;""" % (
        trade_name, startep, endep
    ))
        trades_df['result'] = trades_df['result'].map({'lose': -1, 'win': 1})

        features = []
        for _, row in trades_df.iterrows():
            df = db.read_sql("""WITH a AS (
select EP, O, H, L, C
FROM %s
WHERE EP < %d
AND codename = '%s'
ORDER BY EP desc LIMIT %d
)
select * from a order by EP asc
;""" % (tablename, row["open_epoch"], row["codename"], n_candles))
            del df['ep']
            ohlcv_data = df.values.tolist()
            flattened_data = [item for sublist in ohlcv_data for item in sublist]
            scaler = MinMaxScaler()
            flattened_data = np.array(flattened_data)
            flattened_data = scaler.fit_transform(flattened_data.reshape(-1, 1)).flatten()
            features.append(flattened_data)

        X = pd.DataFrame(features)
        y = pd.Series(trades_df['result'])

        


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
        n_candles = 60
        Random Forest: 0.49 (+/- 0.03)
        Logistic Regression: 0.52 (+/- 0.05)
        SVM: 0.51 (+/- 0.01)
        KNN: 0.50 (+/- 0.07)

        n_candles = 20
        Random Forest: 0.56 (+/- 0.08)
        Logistic Regression: 0.57 (+/- 0.05)
        SVM: 0.56 (+/- 0.06)
        KNN: 0.52 (+/- 0.07)

        n_candles = 5
        Random Forest: 0.52 (+/- 0.04)
        Logistic Regression: 0.58 (+/- 0.05)
        SVM: 0.55 (+/- 0.02)
        KNN: 0.50 (+/- 0.05)
        """


        #X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        #clf = RandomForestClassifier(n_estimators=100, random_state=42)
        #clf.fit(X_train, y_train)
        #y_pred = clf.predict(X_test)

        #accuracy = accuracy_score(y_test, y_pred)
        #print(f'Accuracy: {accuracy * 100:.2f}%')
