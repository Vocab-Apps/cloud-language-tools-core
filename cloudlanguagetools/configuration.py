"""Service configuration for cloudlanguagetools.

A single, versioned pydantic model (`ServicesConfiguration`) enables services and holds their
credentials. Every service has an optional sub-model: a service is enabled when its sub-model is
present, and disabled (never consulted, and raising `ServiceNotEnabledError` when called directly)
when it is left out.

Validation is structural only: required fields must be present and non-empty, the API keys are
not checked against the services.

    configuration = ServicesConfiguration(
        azure=AzureConfig(api_key='...', region='eastus'),
        mandarin_cantonese=MandarinCantoneseConfig(),
    )
    manager = cloudlanguagetools.servicemanager.ServiceManager(configuration)

The same configuration as JSON (what `ServicesConfiguration.model_validate_json` accepts and
`dump_json` produces):

    {"version": 1, "azure": {"api_key": "...", "region": "eastus"}, "mandarin_cantonese": {}}
"""

from typing import Annotated, Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, SecretStr, StringConstraints

from cloudlanguagetools.constants import Service

CONFIGURATION_VERSION = 1

# a non-empty string, surrounding whitespace removed
NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

# a non-empty secret: hidden in repr/str (so keys don't end up in logs), but serialized in clear
# so that a configuration can round-trip through JSON (and through encryption.py)
Secret = Annotated[
    SecretStr,
    Field(min_length=1),
    PlainSerializer(lambda value: value.get_secret_value(), return_type=str),
]


class ServiceConfig(BaseModel):
    """Base class of all per-service configuration models."""
    model_config = ConfigDict(extra='forbid', frozen=True)


# services which require credentials
# ==================================

class AzureConfig(ServiceConfig):
    api_key: Secret
    region: NonEmptyStr


class GoogleConfig(ServiceConfig):
    """Google Cloud Text-to-Speech and Cloud Translation (v2).

    api_key: a Google Cloud API key allowed to call the Cloud Text-to-Speech API and the
    Cloud Translation API.
    """
    api_key: Secret


class GeminiConfig(ServiceConfig):
    """Gemini TTS, through the Gemini API (generativelanguage.googleapis.com).

    api_key: a Gemini API key (Google AI Studio).
    """
    api_key: Secret


class WatsonConfig(ServiceConfig):
    translator_api_key: Secret
    translator_url: NonEmptyStr
    speech_api_key: Secret
    speech_url: NonEmptyStr


class NaverConfig(ServiceConfig):
    # Clova voice (TTS)
    client_id: NonEmptyStr
    client_secret: Secret
    # Papago (translation)
    papago_translation_client_id: NonEmptyStr
    papago_translation_client_secret: Secret


class AmazonConfig(ServiceConfig):
    access_key_id: NonEmptyStr
    secret_access_key: Secret
    region: NonEmptyStr


class ForvoConfig(ServiceConfig):
    api_key: Secret


class CereProcConfig(ServiceConfig):
    username: NonEmptyStr
    password: Secret


class VocalWareConfig(ServiceConfig):
    account_id: NonEmptyStr
    api_id: NonEmptyStr
    secret_phrase: Secret


class FptAiConfig(ServiceConfig):
    api_key: Secret


class ElevenLabsConfig(ServiceConfig):
    api_key: Secret


class EasyPronunciationConfig(ServiceConfig):
    api_key: Secret


class DeepLConfig(ServiceConfig):
    api_key: Secret


class OpenAIConfig(ServiceConfig):
    api_key: Secret
    # Azure OpenAI deployment, not used by the OpenAI service itself (only by debugging utilities)
    azure_api_key: Optional[Secret] = None
    azure_endpoint: Optional[NonEmptyStr] = None
    azure_deployment_name: Optional[NonEmptyStr] = None


class AlibabaConfig(ServiceConfig):
    access_key_id: NonEmptyStr
    access_key_secret: Secret
    app_key: NonEmptyStr


# keyless services, enabled with an empty sub-model
# =================================================

class NlpApiServiceConfig(ServiceConfig):
    # override the URL of the NLP API used by this service (defaults to the hosted vocab.ai API)
    base_url: Optional[NonEmptyStr] = None


class EpitranConfig(NlpApiServiceConfig):
    pass


class SpacyConfig(NlpApiServiceConfig):
    pass


class PyThaiNLPConfig(NlpApiServiceConfig):
    pass


class MandarinCantoneseConfig(ServiceConfig):
    pass


class WenlinConfig(ServiceConfig):
    pass


class TestServiceConfig(ServiceConfig):
    """Mock services which don't make any API calls, for tests."""
    pass


# the top-level model
# ===================

# configuration field name -> Service enum, in the order the services get loaded
SERVICE_FIELDS: Dict[str, Service] = {
    'azure': Service.Azure,
    'google': Service.Google,
    'watson': Service.Watson,
    'naver': Service.Naver,
    'amazon': Service.Amazon,
    'forvo': Service.Forvo,
    'cereproc': Service.CereProc,
    'vocalware': Service.VocalWare,
    'fptai': Service.FptAi,
    'elevenlabs': Service.ElevenLabs,
    'easypronunciation': Service.EasyPronunciation,
    'epitran': Service.Epitran,
    'deepl': Service.DeepL,
    'pythainlp': Service.PyThaiNLP,
    'spacy': Service.Spacy,
    'mandarin_cantonese': Service.MandarinCantonese,
    'wenlin': Service.Wenlin,
    'openai': Service.OpenAI,
    'alibaba': Service.Alibaba,
    'gemini': Service.Gemini,
    'test_service_a': Service.TestServiceA,
    'test_service_b': Service.TestServiceB,
}

KEYLESS_SERVICE_FIELDS = ['epitran', 'pythainlp', 'spacy', 'mandarin_cantonese', 'wenlin']


class ServicesConfiguration(BaseModel):
    """Enables services and configures them. Leave a service out (None) to disable it."""
    model_config = ConfigDict(extra='forbid', frozen=True)

    version: Literal[1] = CONFIGURATION_VERSION

    azure: Optional[AzureConfig] = None
    google: Optional[GoogleConfig] = None
    watson: Optional[WatsonConfig] = None
    naver: Optional[NaverConfig] = None
    amazon: Optional[AmazonConfig] = None
    forvo: Optional[ForvoConfig] = None
    cereproc: Optional[CereProcConfig] = None
    vocalware: Optional[VocalWareConfig] = None
    fptai: Optional[FptAiConfig] = None
    elevenlabs: Optional[ElevenLabsConfig] = None
    easypronunciation: Optional[EasyPronunciationConfig] = None
    epitran: Optional[EpitranConfig] = None
    deepl: Optional[DeepLConfig] = None
    pythainlp: Optional[PyThaiNLPConfig] = None
    spacy: Optional[SpacyConfig] = None
    mandarin_cantonese: Optional[MandarinCantoneseConfig] = None
    wenlin: Optional[WenlinConfig] = None
    openai: Optional[OpenAIConfig] = None
    alibaba: Optional[AlibabaConfig] = None
    gemini: Optional[GeminiConfig] = None
    test_service_a: Optional[TestServiceConfig] = None
    test_service_b: Optional[TestServiceConfig] = None

    def get_service_config(self, service: Service) -> Optional[ServiceConfig]:
        return getattr(self, get_field_name(service))

    def is_enabled(self, service: Service) -> bool:
        return self.get_service_config(service) is not None

    def enabled_services(self) -> Dict[Service, ServiceConfig]:
        """The enabled services and their configuration, in load order."""
        result = {}
        for field_name, service in SERVICE_FIELDS.items():
            service_config = getattr(self, field_name)
            if service_config is not None:
                result[service] = service_config
        return result

    def dump_json(self, **kwargs) -> str:
        """Serialize to JSON, secrets in clear, disabled services omitted."""
        return self.model_dump_json(exclude_none=True, **kwargs)

    @classmethod
    def with_keyless_services(cls, **kwargs) -> 'ServicesConfiguration':
        """A configuration with all the services that don't need an API key enabled, plus kwargs."""
        keyless = {
            'epitran': EpitranConfig(),
            'pythainlp': PyThaiNLPConfig(),
            'spacy': SpacyConfig(),
            'mandarin_cantonese': MandarinCantoneseConfig(),
            'wenlin': WenlinConfig(),
        }
        return cls(**{**keyless, **kwargs})


def get_field_name(service: Service) -> str:
    for field_name, field_service in SERVICE_FIELDS.items():
        if field_service == service:
            return field_name
    raise KeyError(f'service {service} cannot be configured')


def load_configuration(data: Dict[str, Any]) -> ServicesConfiguration:
    """Validate configuration data (a dict, e.g. parsed JSON). Data without a `version` key is
    treated as the legacy services_configuration.json format and converted."""
    if 'version' not in data:
        return from_legacy_dict(data)
    return ServicesConfiguration.model_validate(data)


# legacy format
# =============

def from_legacy_dict(legacy: Dict[str, Any]) -> ServicesConfiguration:
    """Convert the legacy services_configuration.json format (keyed by Service enum name, with
    service-specific key names) to a ServicesConfiguration.

    The keyless services are all enabled, as in the legacy ServiceManager. Google and Gemini are
    left disabled: the legacy format holds a Google service account, and these services now only
    accept API keys. Legacy entries for services which are not loaded by the ServiceManager
    (e.g. Voicen) are ignored.
    """
    config: Dict[str, Any] = {field_name: {} for field_name in KEYLESS_SERVICE_FIELDS}

    def section(name):
        return legacy.get(name)

    if (azure := section('Azure')) is not None:
        config['azure'] = {'api_key': azure['key'], 'region': azure['region']}
    if (watson := section('Watson')) is not None:
        config['watson'] = dict(watson)
    if (naver := section('Naver')) is not None:
        config['naver'] = dict(naver)
    if (amazon := section('Amazon')) is not None:
        config['amazon'] = {
            'access_key_id': amazon['AWS_ACCESS_KEY_ID'],
            'secret_access_key': amazon['AWS_SECRET_ACCESS_KEY'],
            'region': amazon['AWS_DEFAULT_REGION'],
        }
    if (forvo := section('Forvo')) is not None:
        config['forvo'] = {'api_key': forvo['key']}
    if (cereproc := section('CereProc')) is not None:
        config['cereproc'] = dict(cereproc)
    if (vocalware := section('VocalWare')) is not None:
        config['vocalware'] = dict(vocalware)
    if (fptai := section('FptAi')) is not None:
        config['fptai'] = {'api_key': fptai['key']}
    if (elevenlabs := section('ElevenLabs')) is not None:
        config['elevenlabs'] = {'api_key': elevenlabs['api_key']}
    if (easypronunciation := section('EasyPronunciation')) is not None:
        config['easypronunciation'] = {'api_key': easypronunciation['api_key']}
    if (deepl := section('DeepL')) is not None:
        config['deepl'] = {'api_key': deepl['key']}
    if (openai := section('OpenAI')) is not None:
        config['openai'] = dict(openai)
    if (alibaba := section('Alibaba')) is not None:
        config['alibaba'] = dict(alibaba)

    return ServicesConfiguration.model_validate(config)
