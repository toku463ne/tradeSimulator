CREATE TABLE IF NOT EXISTS zz_predicts (
    trade_name VARCHAR(50),
    "name" VARCHAR(50),
    startep INT,
    endep INT,
    startdt TIMESTAMP,
    enddt TIMESTAMP,
    samples INT,
    n_ups INT,
    n_downs INT,
    threshold FLOAT,
    high_accuracy FLOAT,
    high_count_above_threshold INT,
    low_accuracy FLOAT,
    low_count_above_threshold INT,
    PRIMARY KEY (trade_name, codename, startep, endep)
);