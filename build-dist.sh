#!/bin/bash

rm -rf ./build

set -eo pipefail

PYTHON_BIN=${PYTHON_BIN:-python3}

echo "$PYTHON_BIN"

set -x

cd "$PROJECT"
$PYTHON_BIN setup.py sdist bdist_wheel

set +x