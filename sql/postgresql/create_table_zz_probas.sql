CREATE TABLE IF NOT EXISTS zz_probas (
    order_id VARCHAR(100), 
    proba_all FLOAT,
    proba_group FLOAT,
    proba_kobetsu FLOAT,
    PRIMARY KEY (order_id)
);