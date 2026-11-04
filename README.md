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
    gemini=GeminiConfig(api_key='...'),  # a Gemini API key from Google AI Studio
)
manager = cloudlanguagetools.servicemanager.ServiceManager(configuration)
# reconfigure later (e.g. after the user changed their keys): manager.configure(new_configuration)
```

The same configuration as JSON (`ServicesConfiguration.model_validate_json` / `configuration.dump_json()`):

```json
{"version": 1, "azure": {"api_key": "...", "region": "eastus"}, "mandarin_cantonese": {}}
```

Google and Gemini are configured separately, each with an API key (service accounts are not supported):
- `GoogleConfig(api_key=...)`: a Google Cloud API key allowed to call the Cloud Text-to-Speech API
  and the Cloud Translation API.
- `GeminiConfig(api_key=...)`: a Gemini API key (Google AI Studio). All Gemini models go through the
  Gemini API.

## service keys (backend deployment)
The backend's configuration is stored encrypted in `cloudlanguagetools/keys.py`, keyed by the
`CLOUDLANGUAGETOOLS_CORE_KEY` environment variable (`cloudlanguagetools.encryption.EncryptionSettings`).

```python
configuration = cloudlanguagetools.encryption.load_configuration()
manager = cloudlanguagetools.servicemanager.ServiceManager(configuration)
```

Edit / re-encrypt it with utils/service_keys.py (`--action decrypt_write_json`, edit
`services_configuration.json`, `--action encrypt`).

## CLT-AI API

A versioned, LLM friendly API in `cloudlanguagetools.cltai`:

```python
from cloudlanguagetools.cltai import create_client, CltAPIVersion, SoundRequest, TranslateRequest
clt = create_client(CltAPIVersion.v1, manager=manager)  # manager: a configured ServiceManager, see above
sound = clt.sound(SoundRequest(text='今日はいい天気ですね', language='ja', gender='Female'))
print(sound.audio_path, sound.service, sound.voice_key)
print(clt.translate(TranslateRequest(text='bonjour', source_language='fr', target_language='en')).text)
print(clt.describe_api())
```

The CLT-AI Agent turns instructions into repeatable python transformations, or answers directly:

```python
from cloudlanguagetools.cltai.agent import CltAIAgent
agent = CltAIAgent(clt)
transformation = agent.generate_transformation('generate pinyin for the Chinese field', sample_row={'Chinese': '你好', 'Pinyin': ''})
transformation.run_rows(clt, rows)
response = agent.run_instant('成本很低', standing_instructions='translate chinese to english, give me pinyin and audio')
```

## building releases
see package.sh
