#!/usr/bin/bash
appdir=$1
cat << EOF > /etc/systemd/system/tradesimulator.service
[Unit]
Description=wsgi for Stockanalyzer api 

# Requirements
Requires=network.target

# Dependency ordering
After=network.target

[Service]
TimeoutStartSec=0
RestartSec=10
Restart=always

# path to app
WorkingDirectory=$appdir
# the user that you want to run app by
User=root

KillSignal=SIGQUIT
Type=notify
NotifyAccess=all

# Main process
ExecStart=$appdir/.venv/bin/uwsgi -c $appdir/uwsgi.ini

[Install]
WantedBy=multi-user.target
EOF