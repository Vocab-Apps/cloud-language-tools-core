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