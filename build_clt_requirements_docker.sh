#!/bin/bash

# exit if an argument is not passed
if [ -z "$1" ]; then
    echo "Please provide a version number"
    exit 1
fi

CLT_REQUIREMENTS_VERSION=$1 # for example 0.1

export DOCKER_BUILDKIT=1
DOCKER_IMAGE=vocabai/clt-requirements
docker build -t ${DOCKER_IMAGE}:${CLT_REQUIREMENTS_VERSION} --build-arg CLT_REQUIREMENTS_VERSION=${CLT_REQUIREMENTS_VERSION} -f Dockerfile.clt_requirements .
docker push ${DOCKER_IMAGE}:${CLT_REQUIREMENTS_VERSION}