import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse

import cloudlanguagetools
import cloudlanguagetools.encryption

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='encrypt / decrypt the service configuration stored in cloudlanguagetools/keys.py')
    parser.add_argument('--action', choices=['encrypt', 'decrypt', 'decrypt_write_json'], required=True)

    args = parser.parse_args()

    if args.action == 'encrypt':
        cloudlanguagetools.encryption.encrypt()
    elif args.action == 'decrypt':
        # validates the stored configuration and lists the enabled services (no secrets printed)
        configuration = cloudlanguagetools.encryption.load_configuration()
        print(', '.join(service.name for service in configuration.enabled_services()))
    elif args.action == 'decrypt_write_json':
        cloudlanguagetools.encryption.decrypt_write_json()
