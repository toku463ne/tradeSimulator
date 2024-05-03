CREATE DATABASE tradesimulator;
CREATE DATABASE tradesimulator_test;

CREATE USER tradeuser WITH PASSWORD 'tradepass';
\c tradesimulator;
GRANT ALL PRIVILEGES ON DATABASE tradesimulator TO tradeuser;
CREATE EXTENSION IF NOT EXISTS timescaledb;

\c tradesimulator_test;
GRANT ALL PRIVILEGES ON DATABASE tradesimulator TO tradeuser;
CREATE EXTENSION IF NOT EXISTS timescaledb;

