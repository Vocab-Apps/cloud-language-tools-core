#!/bin/bash

# exit if parameter is not passed in
if [ -z "$1" ]; then
    echo "Please provide a version number"
    exit 1
fi

VERSION_NUMBER=$1 # for example 0.1

# build docker image
export DOCKER_BUILDKIT=1
docker build -t vocabai/cloud-language-tools-core:${VERSION_NUMBER} --build-arg CLT_CORE_VERSION=${VERSION_NUMBER} -f Dockerfile.clt_core .
docker push vocabai/cloud-language-tools-core:${VERSION_NUMBER}