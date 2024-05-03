CREATE TABLE IF NOT EXISTS trades (
    "trade_name" VARCHAR(50),
    "order_id" VARCHAR(100),
    "codename" VARCHAR(50),
    "result" VARCHAR(10),
    "profit" FLOAT,
    "side" SMALLINT,
    "units" FLOAT,
    "expiration_epoch" INT,
    "expiration_datetime" TIMESTAMP,
    "open_price" FLOAT,
    "open_epoch" INT,
    "open_datetime" TIMESTAMP,
    "open_desc" VARCHAR(100),
    "takeprofit_price" FLOAT,
    "stoploss_price" FLOAT,
    "close_price" FLOAT,
    "close_epoch" INT,
    "close_datetime" TIMESTAMP,
    "close_desc" VARCHAR(100),
    PRIMARY KEY(trade_name, order_id)
);