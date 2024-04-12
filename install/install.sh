#!/bin/bash

set -e

echo apt update
sudo apt update
echo apt -y install nodejs npm python3-pip python3-venv mariadb-server build-essential libssl-dev libffi-dev libssl-dev libmysqlclient-dev net-tools 
sudo apt -y install nodejs npm python3-pip python3-venv mariadb-server build-essential libssl-dev libffi-dev libssl-dev libmysqlclient-dev net-tools

plugindir=`sudo mysql -sN -e "select @@plugin_dir;"`

echo mkdir -p /usr/local/src/git
sudo mkdir -p /usr/local/src/git
sudo rm -rf /usr/local/src/git/mysql-trimmean
echo git clone https://github.com/StirlingMarketingGroup/mysql-trimmean.git
sudo bash -c 'cd /usr/local/src/git && git clone https://github.com/StirlingMarketingGroup/mysql-trimmean.git'
echo "gcc -O3 -I/usr/include/mysql -o trimmean.so -shared trimmean.c -fPIC"
sudo bash -c 'cd /usr/local/src/git/mysql-trimmean && gcc -O3 -I/usr/include/mysql -o trimmean.so -shared trimmean.c -fPIC'
echo cp /usr/local/src/git/mysql-trimmean/trimmean.so $plugindir
sudo cp /usr/local/src/git/mysql-trimmean/trimmean.so $plugindir

set +e
echo mysql -e "create aggregate function trimmean returns real soname'trimmean.so';"
sudo mysql -e "CREATE AGGREGATE FUNCTION trimmean RETURNS REAL SONAME 'trimmean.so';"

echo 'mysql  < sql/init_database.sql'
sudo mysql  < sql/init_database.sql
set -e

echo python3 -m venv .venv
python3 -m venv .venv


echo source .venv/bin/activate
source .venv/bin/activate

echo pip3 install pymysql yfinance pandas_datareader pandas numpy sqlalchemy falcon xlrd path scikit-learn tzlocal pytz
pip3 install -r install/pip/requirements.txt

echo install grafana
echo "apt-get install -y apt-transport-https software-properties-common wget"
sudo apt-get install -y apt-transport-https software-properties-common wget
echo "mkdir -p /etc/apt/keyrings/"
sudo mkdir -p /etc/apt/keyrings/

echo "wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor > /usr/share/keyrings/grafana.gpg"
curl -fsSL https://packages.grafana.com/gpg.key|sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/grafana.gpg
#sudo bash -c "echo 'deb https://packages.grafana.com/oss/deb stable main' > /etc/apt/sources.list.d/grafana.list"
sudo add-apt-repository  -y "deb https://packages.grafana.com/oss/deb stable main"

# Updates the list of available packages
echo apt-get update
sudo apt-get update
echo apt-get install -y grafana-nightly
sudo apt-get install -y grafana-nightly

echo installation succeeded!
