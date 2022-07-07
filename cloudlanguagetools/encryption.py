import os
import json
import cryptography
import cryptography.fernet
import cloudlanguagetools.keys

SERVICES_CONFIGURATION_JSON = 'services_configuration.json'

def get_key():
    return os.environ['CLOUDLANGUAGETOOLS_CORE_KEY']

def encrypt():
    # open json file
    f = open(SERVICES_CONFIGURATION_JSON)
    config = json.load(f)
    f.close()    
    config_str = json.dumps(config)

    # encrypt    
    f = cryptography.fernet.Fernet(get_key())
    token = f.encrypt(config_str.encode('utf-8'))

    # write to python module
    keys_module_path = os.path.join(os.path.dirname(__file__), 'keys.py')
    f = open(keys_module_path, 'w')
    f.write(f"KEYS='{token.decode('utf-8')}'")
    f.close()

def decrypt():
    f = cryptography.fernet.Fernet(get_key())
    decoded_bytes = f.decrypt(cloudlanguagetools.keys.KEYS.encode('utf-8'))
    decoded_str = decoded_bytes.decode('utf-8')
    return json.loads(decoded_str)

def decrypt_write_json():
    f = open(SERVICES_CONFIGURATION_JSON, 'w')
    json.dump(decrypt(), f, indent=4)
    f.close()
