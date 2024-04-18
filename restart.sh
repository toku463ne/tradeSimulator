#!/usr/bin/bash

set -e

echo systemctl restart tradesimulator
sudo systemctl restart tradesimulator

echo systemctl restart nginx
sudo systemctl restart nginx

echo "OK!"