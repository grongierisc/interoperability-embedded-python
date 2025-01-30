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

cd src

# print iris version
echo "IRIS version:"
python3 -c "import iris; print(iris.system.Version.GetVersion())"

# setup the environment
python3 -m iop --init
exit_on_error

# Unit tests
cd ..
python3 -m pytest
exit_on_error

# Integration tests
cd src
python3 -m iop --migrate ../demo/python/reddit/settings.py
exit_on_error

python3 -m iop --default PEX.Production
exit_on_error

python3 -m iop --start PEX.Production --detach
exit_on_error

python3 -m iop --log 10

python3 -m iop -S
exit_on_error

iris_stop