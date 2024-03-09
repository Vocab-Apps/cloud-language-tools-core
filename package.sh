#!/bin/bash
set -eoux pipefail

VERSION_NUMBER=`bump --major`
echo "new version number is ${VERSION_NUMBER}"
GIT_TAG=v${VERSION_NUMBER}

git commit -a -m "upgraded version to ${VERSION_NUMBER}"
git push
git tag -a ${GIT_TAG} -m "version ${GIT_TAG}"
git push origin ${GIT_TAG}

# build python module , upload to pypi
# get twine user/password
source ~/secrets/python/twine.sh
python setup.py sdist
twine upload dist/cloudlanguagetools-${VERSION_NUMBER}.tar.gz

# build clt-core docker image
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
${SCRIPT_DIR}/build_clt_core_docker.sh ${VERSION_NUMBER}

# run test using docker
${SCRIPT_DIR}/run_clt_docker.test.sh ${VERSION_NUMBER}

