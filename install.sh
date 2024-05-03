#!/bin/bash

set -e

pydir=$(pwd)

export appdir=/usr/local/tradesimulator
echo appdir is $appdir/
sudo mkdir -p $appdir

curuser=`whoami`
sudo chown $curuser:$curuser $appdir

pkgs="gnupg postgresql-common postgresql-client apt-transport-https lsb-release wget \
npm python3-pip python3-venv mariadb-server nginx build-essential libpq-dev \
libssl-dev libffi-dev libssl-dev libmysqlclient-dev net-tools \
adminer php8.1 php8.1-fpm php8.1-mysql php8.1-xml php8.1-mbstring"

echo apt update
sudo apt update
echo apt -y install $pkgs 
sudo apt -y install $pkgs

echo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh

echo "deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main" | sudo tee /etc/apt/sources.list.d/timescaledb.list
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo apt-key add -
echo apt update
sudo apt update

echo apt install timescaledb-2-postgresql-14
sudo apt install timescaledb-2-postgresql-14


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

#echo 'mysql  < sql/mysql/init_database.sql'
#sudo mysql  < sql/mysql/init_database.sql

echo "shared_preload_libraries = 'timescaledb'"
sudo sed -i "s/#shared_preload_libraries = ''/shared_preload_libraries = 'timescaledb'/g" /etc/postgresql/14/main/postgresql.conf

echo systemctl restart postgresql@14-main
sudo systemctl restart postgresql@14-main

echo "postgres psql < sql/postgresql/init_database.sql"
sudo -u postgres psql < sql/postgresql/init_database.sql
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
