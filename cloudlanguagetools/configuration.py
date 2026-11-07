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

import enum
from typing import Annotated, Dict, Literal, Optional

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


# cloud regions
# =============

class AzureRegion(enum.StrEnum):
    """Azure regions of the Speech service (speech to text, text to speech, translation), the
    region of the Azure Speech / AI Services resource the key belongs to.
    https://learn.microsoft.com/en-us/azure/ai-services/speech-service/regions"""
    southafricanorth = 'southafricanorth'
    eastasia = 'eastasia'
    southeastasia = 'southeastasia'
    australiaeast = 'australiaeast'
    centralindia = 'centralindia'
    japaneast = 'japaneast'
    japanwest = 'japanwest'
    koreacentral = 'koreacentral'
    canadacentral = 'canadacentral'
    canadaeast = 'canadaeast'
    northeurope = 'northeurope'
    westeurope = 'westeurope'
    francecentral = 'francecentral'
    germanywestcentral = 'germanywestcentral'
    italynorth = 'italynorth'
    norwayeast = 'norwayeast'
    swedencentral = 'swedencentral'
    switzerlandnorth = 'switzerlandnorth'
    switzerlandwest = 'switzerlandwest'
    uksouth = 'uksouth'
    ukwest = 'ukwest'
    uaenorth = 'uaenorth'
    brazilsouth = 'brazilsouth'
    qatarcentral = 'qatarcentral'
    centralus = 'centralus'
    eastus = 'eastus'
    eastus2 = 'eastus2'
    northcentralus = 'northcentralus'
    southcentralus = 'southcentralus'
    westcentralus = 'westcentralus'
    westus = 'westus'
    westus2 = 'westus2'
    westus3 = 'westus3'


class AmazonRegion(enum.StrEnum):
    """AWS regions of Amazon Polly (text to speech), from botocore's endpoint data. Amazon Translate
    is available in a subset of these (not in af-south-1, ap-northeast-3, ap-southeast-5,
    ap-southeast-7, eu-central-2, eu-south-2, me-south-1, sa-east-1)."""
    af_south_1 = 'af-south-1'
    ap_east_1 = 'ap-east-1'
    ap_northeast_1 = 'ap-northeast-1'
    ap_northeast_2 = 'ap-northeast-2'
    ap_northeast_3 = 'ap-northeast-3'
    ap_south_1 = 'ap-south-1'
    ap_southeast_1 = 'ap-southeast-1'
    ap_southeast_2 = 'ap-southeast-2'
    ap_southeast_5 = 'ap-southeast-5'
    ap_southeast_7 = 'ap-southeast-7'
    ca_central_1 = 'ca-central-1'
    eu_central_1 = 'eu-central-1'
    eu_central_2 = 'eu-central-2'
    eu_north_1 = 'eu-north-1'
    eu_south_2 = 'eu-south-2'
    eu_west_1 = 'eu-west-1'
    eu_west_2 = 'eu-west-2'
    eu_west_3 = 'eu-west-3'
    me_south_1 = 'me-south-1'
    sa_east_1 = 'sa-east-1'
    us_east_1 = 'us-east-1'
    us_east_2 = 'us-east-2'
    us_west_1 = 'us-west-1'
    us_west_2 = 'us-west-2'


# services which require credentials
# ==================================

class AzureConfig(ServiceConfig):
    api_key: Secret
    region: AzureRegion


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
    region: AmazonRegion


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
