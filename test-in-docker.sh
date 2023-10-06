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

# Test
python3 -m pytest
exit_on_error

iris_stop