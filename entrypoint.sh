#!/bin/bash

set -m

/usr/irissys/dev/Cloud/ICM/waitISC.sh

# init iop
iop --init

# load production
iop -m /irisdev/app/demo/python/reddit/settings.py

# set default production
iop --default PEX.Production

# start production
iop --start &

fg %1