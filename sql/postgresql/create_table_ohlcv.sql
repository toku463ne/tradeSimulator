CREATE TABLE IF NOT EXISTS #TABLENAME# (
    codename VARCHAR(50),
    EP INT NOT NULL,
    DT TIMESTAMP, 
    O FLOAT,
    H FLOAT,
    L FLOAT,
    C FLOAT,
    V BIGINT,
    PRIMARY KEY (codename, EP)
);