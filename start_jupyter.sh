#!/bin/bash

export appdir=/usr/local/tradesimulator
echo source $appdir/.venv/bin/activate
source $appdir/.venv/bin/activate

jupyter-lab --ip='0.0.0.0'



