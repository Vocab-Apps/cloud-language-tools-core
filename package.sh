#!/bin/bash
set -eoux pipefail

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

# wait for package to be updated on pypi
python utils/wait_pypi_version_update.py --package cloudlanguagetools --version ${VERSION_NUMBER}

# get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
${SCRIPT_DIR}/build_clt_core_docker.sh ${VERSION_NUMBER}
