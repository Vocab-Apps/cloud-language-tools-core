import requests
import argparse
import pprint
import time
import sys

def get_releases(package_name):
    pypi_url = f'https://pypi.org/pypi/{package_name}/json'
    response = requests.get(pypi_url)
    response.raise_for_status()
    return response.json()['releases'].keys()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Wait until module on pypi is updated to correct version')
    parser.add_argument('--package', required=True)
    parser.add_argument('--version', required=True)

    args = parser.parse_args()

    package_name = args.package
    package_version = args.version


    version_available = False
    max_iterations = 30
    while not version_available and max_iterations > 0:
        releases = get_releases(package_name)
        if package_version in releases:
            print(f'Version {package_version} of {package_name} is available')
            version_available = True
        else:
            print(f'Version {package_version} of {package_name} is not available yet, sleeping')
            time.sleep(1)
            max_iterations -= 1

    if max_iterations == 0:
        sys.exit(1)