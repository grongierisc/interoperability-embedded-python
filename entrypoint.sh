#!/bin/bash

# start iris
/iris-main "$@" &

/usr/irissys/dev/Cloud/ICM/waitISC.sh

alias iop='irispython -m iop'

# init iop
iop --init

# load production
iop -m /irisdev/app/demo/python/reddit/settings.py

# set default production
iop --default PEX.Production

# start production
iop --start 

