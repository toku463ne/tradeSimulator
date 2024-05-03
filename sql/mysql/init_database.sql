CREATE DATABASE tradesimulator CHARACTER SET 'utf8';
CREATE DATABASE tradesimulator_test CHARACTER SET 'utf8';
CREATE USER IF NOT EXISTS 'tradeuser'@'%' IDENTIFIED BY 'tradepass';
GRANT ALL PRIVILEGES ON tradesimulator.* to 'tradeuser'@'%';
GRANT ALL PRIVILEGES ON tradesimulator_test.* to 'tradeuser'@'%';

