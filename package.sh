#!/bin/bash
set -eoux pipefail

# ensure we are on the main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
  echo "Error: must be on the main branch to package (currently on '$CURRENT_BRANCH')"
  exit 1
fi

# bump version argument
# default should be patch, but could be major or minor
BUMP_TYPE=${1:-patch}

# bump rewrites [project].version in pyproject.toml and echoes the new version
VERSION_NUMBER=$(uv run --no-sync bump --${BUMP_TYPE} --reset)
echo "new version number is ${VERSION_NUMBER}"
GIT_TAG=v${VERSION_NUMBER}

# refresh uv.lock so it records the new project version. this must happen before the
# commit, otherwise `uv export --frozen` inside the docker build fails on a stale lock.
uv lock

git commit -a -m "upgraded version to ${VERSION_NUMBER}"
git push
git tag -a ${GIT_TAG} -m "version ${GIT_TAG}"
git push origin ${GIT_TAG}

# build sdist + wheel, upload to pypi
# get pypi user/password
source ${SECRETS_DIR}/python/twine.sh
rm -rf dist
uv build
uv publish -u "${TWINE_USERNAME}" -p "${TWINE_PASSWORD}" \
    dist/cloudlanguagetools-${VERSION_NUMBER}.tar.gz \
    dist/cloudlanguagetools-${VERSION_NUMBER}-py3-none-any.whl

# build clt-core docker image
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
${SCRIPT_DIR}/build_clt_core_docker.sh ${VERSION_NUMBER}

# run test using docker
${SCRIPT_DIR}/run_clt_docker.test.sh ${VERSION_NUMBER}

# print output
GREEN='\033[0;32m'
NC='\033[0m' # No Color
echo -e "cloud-language-tools-core version ${GREEN}${VERSION_NUMBER}${NC} passed tests."
