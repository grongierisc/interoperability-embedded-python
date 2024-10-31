#!/bin/bash

rm -rf ./build

packages=("intersystems_iris" "irisnative")
for package in ${packages[@]};
do
    rm -f ./src/$package
    package_path=`python -c "import importlib.util; print(importlib.util.find_spec('${package}').submodule_search_locations[0])"`
    ln -s $package_path ./src/$package
done

set -eo pipefail

PYTHON_BIN=${PYTHON_BIN:-python3}

echo "$PYTHON_BIN"

set -x

cd "$PROJECT"
$PYTHON_BIN setup.py sdist bdist_wheel

for package in ${packages[@]};
do
    rm -f ./src/$package
done

set +x