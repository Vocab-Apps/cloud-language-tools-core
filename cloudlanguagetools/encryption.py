"""Encrypted service configuration, for the backend deployment.

The ServicesConfiguration is stored encrypted (Fernet) in cloudlanguagetools/keys.py. The
encryption key comes from the CLOUDLANGUAGETOOLS_CORE_KEY environment variable, see
EncryptionSettings.

    configuration = cloudlanguagetools.encryption.load_configuration()
    manager = cloudlanguagetools.servicemanager.ServiceManager(configuration)
"""

import os
import base64
import binascii
from typing import Mapping, Optional

import pydantic
from pydantic import BaseModel, ConfigDict, SecretStr
import cryptography.fernet

import cloudlanguagetools.configuration
import cloudlanguagetools.keys

SERVICES_CONFIGURATION_JSON = 'services_configuration.json'
KEYS_MODULE_PATH = os.path.join(os.path.dirname(__file__), 'keys.py')
KEY_ENVIRONMENT_VARIABLE = 'CLOUDLANGUAGETOOLS_CORE_KEY'


class EncryptionSettings(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)

    # Fernet key: 32 bytes, url-safe base64 encoded
    key: SecretStr

    @pydantic.field_validator('key')
    @classmethod
    def validate_fernet_key(cls, value: SecretStr) -> SecretStr:
        try:
            decoded = base64.urlsafe_b64decode(value.get_secret_value().encode('utf-8'))
        except (binascii.Error, ValueError) as e:
            raise ValueError('encryption key must be url-safe base64 encoded') from e
        if len(decoded) != 32:
            raise ValueError('encryption key must be 32 url-safe base64-encoded bytes (see cryptography.fernet.Fernet.generate_key)')
        return value

    @classmethod
    def from_environment(cls, environ: Optional[Mapping[str, str]] = None) -> 'EncryptionSettings':
        environ = os.environ if environ is None else environ
        if KEY_ENVIRONMENT_VARIABLE not in environ:
            raise KeyError(f'environment variable {KEY_ENVIRONMENT_VARIABLE} is not set')
        return cls(key=environ[KEY_ENVIRONMENT_VARIABLE])

    def get_fernet(self) -> cryptography.fernet.Fernet:
        return cryptography.fernet.Fernet(self.key.get_secret_value())


def encrypt_configuration(configuration: cloudlanguagetools.configuration.ServicesConfiguration,
        settings: EncryptionSettings) -> str:
    token = settings.get_fernet().encrypt(configuration.dump_json().encode('utf-8'))
    return token.decode('utf-8')


def decrypt_configuration(token: str, settings: EncryptionSettings) -> cloudlanguagetools.configuration.ServicesConfiguration:
    """Decrypt and validate a configuration."""
    decoded_str = settings.get_fernet().decrypt(token.encode('utf-8')).decode('utf-8')
    return cloudlanguagetools.configuration.ServicesConfiguration.model_validate_json(decoded_str)


def load_configuration(settings: Optional[EncryptionSettings] = None) -> cloudlanguagetools.configuration.ServicesConfiguration:
    """Load the configuration stored encrypted in cloudlanguagetools/keys.py."""
    if settings is None:
        settings = EncryptionSettings.from_environment()
    return decrypt_configuration(cloudlanguagetools.keys.KEYS, settings)


# used by utils/service_keys.py
# =============================

def encrypt(settings: Optional[EncryptionSettings] = None, json_path: str = SERVICES_CONFIGURATION_JSON,
        keys_module_path: str = KEYS_MODULE_PATH):
    """Validate the configuration in services_configuration.json and write it encrypted to keys.py."""
    if settings is None:
        settings = EncryptionSettings.from_environment()
    with open(json_path) as f:
        configuration = cloudlanguagetools.configuration.ServicesConfiguration.model_validate_json(f.read())
    token = encrypt_configuration(configuration, settings)
    with open(keys_module_path, 'w') as f:
        f.write(f"KEYS='{token}'")


def decrypt_write_json(settings: Optional[EncryptionSettings] = None, json_path: str = SERVICES_CONFIGURATION_JSON):
    """Write the configuration stored in keys.py to services_configuration.json, in the current format."""
    configuration = load_configuration(settings)
    with open(json_path, 'w') as f:
        f.write(configuration.dump_json(indent=4))
