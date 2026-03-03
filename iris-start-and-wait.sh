#!/bin/bash
# Starts IRIS, initialises IOP (registers the /api/iop REST web app),
# then idles indefinitely.  Used as the container entrypoint in CI so
# that remote e2e tests can be run against it from the outside via
# `docker exec`.

set -e

iris start iris
iris merge iris merge.cpf

cd /irisdev/app/src
python3 -m iop --init

echo "IRIS is ready — /api/iop REST API available on port 52773"

# Block forever; the container will be stopped explicitly by the CI job.
tail -f /dev/null
