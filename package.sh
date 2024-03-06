#!/bin/bash

# exit if parameter is not passed in
if [ -z "$1" ]; then
    echo "Please provide a version number"
    exit 1
fi

VERSION_NUMBER=$1 # for example 0.1
GIT_TAG=v${VERSION_NUMBER}

sed -i "s/version='.*',/version='${VERSION_NUMBER}',/g" setup.py
git commit -a -m "upgraded version to ${VERSION_NUMBER}"
git push
git tag -a ${GIT_TAG} -m "version ${GIT_TAG}"
git push origin ${GIT_TAG}

# build python module , upload to pypi
# get twice user/password
source ~/secrets/python/twine.sh
python setup.py sdist
twine upload dist/*

# build docker image
export DOCKER_BUILDKIT=1
docker build -t lucwastiaux/cloud-language-tools-core:${VERSION_NUMBER} --build-arg CLT_CORE_VERSION=${VERSION_NUMBER} -f Dockerfile.clt_core .
docker push lucwastiaux/cloud-language-tools-core:${VERSION_NUMBER}