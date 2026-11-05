# cloud-language-tools
Interface with various cloud APIs for translation, text to speech

## configuring services
Services are enabled and configured with one versioned pydantic model,
`cloudlanguagetools.configuration.ServicesConfiguration`. Each service has an optional
sub-model; leave it out and the service is disabled (it is not consulted for voice / language
lists, and calling it raises `cloudlanguagetools.errors.ServiceNotEnabledError`).

```python
import cloudlanguagetools.servicemanager
from cloudlanguagetools.configuration import ServicesConfiguration, AzureConfig, GeminiConfig

configuration = ServicesConfiguration.with_keyless_services(  # Epitran, Spacy, PyThaiNLP, MandarinCantonese, Wenlin
    azure=AzureConfig(api_key='...', region='eastus'),
    gemini=GeminiConfig(service_account=open('service_account.json').read()),
)
manager = cloudlanguagetools.servicemanager.ServiceManager(configuration)
# reconfigure later (e.g. after the user changed their keys): manager.configure(new_configuration)
```

The same configuration as JSON (`ServicesConfiguration.model_validate_json` / `configuration.dump_json()`):

```json
{"version": 1, "azure": {"api_key": "...", "region": "eastus"}, "mandarin_cantonese": {}}
```

Google and Gemini are configured separately, each with a service account key (the JSON key
file content, as an object or as text); credentials stay in memory.

## service keys (backend deployment)
The backend's configuration is stored encrypted in `cloudlanguagetools/keys.py`, keyed by the
`CLOUDLANGUAGETOOLS_CORE_KEY` environment variable (`cloudlanguagetools.encryption.EncryptionSettings`).

```python
configuration = cloudlanguagetools.encryption.load_configuration()
manager = cloudlanguagetools.servicemanager.ServiceManager(configuration)
```

Edit / re-encrypt it with utils/service_keys.py (`--action decrypt_write_json`, edit
`services_configuration.json`, `--action encrypt`). Configurations in the pre-versioned format
(keyed by service enum name) are converted automatically when loaded.

## building releases
see package.sh
