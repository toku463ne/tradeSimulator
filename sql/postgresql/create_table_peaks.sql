CREATE TABLE IF NOT EXISTS #TABLENAME# (
    codename VARCHAR(50),
    EP INT NOT NULL,
    side INT,
    DT TIMESTAMP,
    price FLOAT,
    PRIMARY KEY (codename, EP, side)
);