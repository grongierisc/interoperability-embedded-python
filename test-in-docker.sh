#!/bin/bash

iris_start () {
  iris start iris

  # Merge cpf file
  iris merge iris merge.cpf
}

iris_stop () {
  echo "Stopping IRIS"
  iris stop iris quietly
}

exit_on_error () {
  exit=$?;
  if [ $exit -ne 0 ]; then
    iris_stop
    exit $exit
  fi
}

iris_start

# run a python command
cd src
python3 -c "from grongier.pex import Utils; Utils.setup()"
exit_on_error

# back to workdir
cd ..

# Unit tests
python3 -m pytest
exit_on_error

# install main package
pip install git+https://github.com/grongierisc/interoperability-embedded-python
# install dependencies
pip install dataclasses_json requests

# Integration tests
iop --migrate demo/python/reddit/settings.py
exit_on_error

iop --default PEX.Production
exit_on_error

iop --start PEX.Production --detach
exit_on_error

iop --log 10

iop -S
exit_on_error

iris_stop