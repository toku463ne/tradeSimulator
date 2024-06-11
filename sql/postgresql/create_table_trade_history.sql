CREATE TABLE IF NOT EXISTS trade_history (
    "trade_name" VARCHAR(50),
    "epoch" INT,
    "reference_datetime" TIMESTAMP, 
    "cmd" VARCHAR(50),
    "order_id" VARCHAR(100),
    "codename" VARCHAR(50),
    "side" SMALLINT,
    "price" FLOAT,
    "units" FLOAT,
    "buy_offline" FLOAT,
    "buy_online" FLOAT,
    "sell_offline" FLOAT,
    "sell_online" FLOAT
);
DO $$
BEGIN
IF NOT EXISTS (SELECT 1 FROM pg_index i JOIN pg_class c ON i.indexrelid = c.oid
                   WHERE c.relname = 'idx_trade_history_tradename') THEN
    CREATE INDEX idx_trade_history_tradename ON trade_history (trade_name);
END IF;
IF NOT EXISTS (SELECT 1 FROM pg_index i JOIN pg_class c ON i.indexrelid = c.oid
                   WHERE c.relname = 'idx_trade_history_reference_datetime') THEN
    CREATE INDEX idx_trade_history_reference_datetime ON trade_history (reference_datetime);
END IF;
END $$;