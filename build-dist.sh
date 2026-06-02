#!/bin/bash

rm -rf ./build ./dist

set -eo pipefail

PYTHON_BIN=${PYTHON_BIN:-python3}

echo "$PYTHON_BIN"

set -x

cd "$PROJECT"
$PYTHON_BIN -m build

set +x
