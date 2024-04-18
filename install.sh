#!/bin/bash

set -e

pydir=$(pwd)

export appdir=/usr/local/tradesimulator
echo appdir is $appdir/
sudo mkdir -p $appdir

curuser=`whoami`
sudo chown $curuser:$curuser $appdir

echo apt update
sudo apt update
echo apt -y install nodejs npm python3-pip python3-venv mariadb-server nginx build-essential libssl-dev libffi-dev libssl-dev libmysqlclient-dev net-tools adminer php8.1 php8.1-fpm php8.1-mysql php8.1-xml php8.1-mbstring
sudo apt -y install nodejs npm python3-pip python3-venv mariadb-server nginx build-essential libssl-dev libffi-dev libssl-dev libmysqlclient-dev net-tools adminer php8.1 php8.1-fpm php8.1-mysql php8.1-xml php8.1-mbstring

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

echo python3 -m venv $appdir/.venv
python3 -m venv $appdir/.venv


echo source $appdir/.venv/bin/activate
source $appdir/.venv/bin/activate

echo pip3 install -r install/pip/requirements.txt
pip3 install -r install/pip/requirements.txt

echo install grafana
echo "apt-get install -y apt-transport-https software-properties-common wget"
sudo apt-get install -y apt-transport-https software-properties-common wget
echo "mkdir -p /etc/apt/keyrings/"
sudo mkdir -p /etc/apt/keyrings/

#echo "wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor > /usr/share/keyrings/grafana.gpg"
#curl -fsSL https://packages.grafana.com/gpg.key|sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/grafana.gpg
#sudo add-apt-repository  -y "deb https://packages.grafana.com/oss/deb stable main"

# Updates the list of available packages
echo apt-get update
sudo apt-get update
#echo apt-get install -y grafana-nightly
#sudo apt-get install -y grafana-nightlyW

echo pip3 install uwsgi
pip3 install uwsgi

echo install/systemd/create_tradesimulator.service.sh $appdir
sudo bash install/systemd/create_tradesimulator.service.sh $appdir
echo systemctl enable tradesimulator
sudo systemctl enable tradesimulator

echo install/uwsgi/create_uwsgi.ini.sh $appdir `pwd`
install/uwsgi/create_uwsgi.ini.sh $appdir `pwd`

#echo ln $(pwd)/pyapi $appdir/pyapi 
#ln -s $(pwd)/pyapi $appdir/pyapi 

echo cp install/nginx/*.conf /etc/nginx/sites-enabled
sudo cp install/nginx/*.conf /etc/nginx/sites-enabled

echo systemctl reload nginx
sudo systemctl reload nginx


echo access http://localhost:8080/adminer for adminer

echo installation succeeded!
