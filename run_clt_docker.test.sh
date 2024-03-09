#!/bin/bash

set -eoux pipefail

# exit if parameter is not passed in
# exit if parameter is not passed in
if [ -z "$1" ]; then
    echo "Please provide a version number"
    exit 1
fi

VERSION_NUMBER=$1 # for example 0.1

export DOCKER_BUILDKIT=1
DOCKER_IMAGE=lucwastiaux/cloud-language-tools-core-test
docker build -t ${DOCKER_IMAGE}:${VERSION_NUMBER} --build-arg CLT_CORE_VERSION=${VERSION_NUMBER} -f Dockerfile.test .
# https://pypi.org/project/pytest-xdist/2.5.0/#features
# --dist load (default): Sends pending tests to any worker that is available, without any guaranteed order.
docker run --env CLOUDLANGUAGETOOLS_CORE_KEY=${CLOUDLANGUAGETOOLS_CORE_KEY} --rm -it ${DOCKER_IMAGE}:${VERSION_NUMBER} pytest -n8 --dist=load tests