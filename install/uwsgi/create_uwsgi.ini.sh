#!/usr/bin/bash
appdir=$1
pydir=$2

echo mkdir -p /var/log/uwsgi
sudo mkdir -p /var/log/uwsgi

cat << EOF > $appdir/uwsgi.ini
[uwsgi]
master = 1
vacuum = true
socket = 127.0.0.1:9001
enable-threads = true
thunder-lock = true
threads = 2
processes = 2
virtualenv = $appdir/.venv
wsgi-file = $pydir/pyapi/uwsgi.py
chdir = $pydir
logto = /var/log/uwsgi/%n.log
uid = root
gid = root
EOF