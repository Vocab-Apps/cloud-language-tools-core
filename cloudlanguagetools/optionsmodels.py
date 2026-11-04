"""Pydantic models describing the service-specific options accepted by each service.

These are used by the CLT-AI API (cloudlanguagetools.cltai) to validate requests before any
API call is made. For TTS, voices already describe their options with a small schema dict
(see options.ParameterType), so the default model is derived from that schema. Services with
fixed options (OpenAI transcription / llm for example) declare explicit models in their module.
"""

import json
import functools
from typing import Any, Dict, Literal, Optional

import pydantic

import cloudlanguagetools.constants
import cloudlanguagetools.options


class ServiceOptions(pydantic.BaseModel):
    """base class for all service options models: unknown options are rejected"""
    model_config = pydantic.ConfigDict(extra='forbid')

    def to_service_options(self) -> Dict[str, Any]:
        """options dict in the format expected by the service implementation (unset values dropped)"""
        return self.model_dump(exclude_none=True)


# the audio format is a top-level parameter of CLT-AI sound requests, not a voice option
EXCLUDED_TTS_OPTIONS = [cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER]


def _option_field(option_name: str, option_spec: Dict[str, Any]):
    option_type = option_spec.get('type')
    default = option_spec.get('default')
    description_parts = []
    field_kwargs = {}
    if option_type == cloudlanguagetools.options.ParameterType.number.name:
        python_type = float
    elif option_type == cloudlanguagetools.options.ParameterType.number_int.name:
        python_type = int
    elif option_type == cloudlanguagetools.options.ParameterType.list.name:
        values = tuple(option_spec.get('values', []))
        python_type = Literal[values] if len(values) > 0 else str
    elif option_type == cloudlanguagetools.options.ParameterType.text.name:
        python_type = str
    else:
        python_type = Any

    if python_type in (float, int):
        if 'min' in option_spec:
            field_kwargs['ge'] = option_spec['min']
        if 'max' in option_spec:
            field_kwargs['le'] = option_spec['max']
    if default is not None:
        description_parts.append(f'service default: {default!r}')
    if 'description' in option_spec:
        description_parts.insert(0, option_spec['description'])

    # every option is optional: when not set, the service uses its own default
    return (Optional[python_type], pydantic.Field(default=None, description='; '.join(description_parts) or None, **field_kwargs))


@functools.lru_cache(maxsize=4096)
def _build_tts_options_model_cached(service_name: str, options_json: str):
    options = json.loads(options_json)
    fields = {}
    for option_name, option_spec in options.items():
        if option_name in EXCLUDED_TTS_OPTIONS:
            continue
        if not option_name.isidentifier():
            continue
        fields[option_name] = _option_field(option_name, option_spec)
    return pydantic.create_model(f'{service_name}TtsOptions', __base__=ServiceOptions, **fields)


def build_tts_options_model(service: cloudlanguagetools.constants.Service, voice_options: Dict[str, Any]) -> type[ServiceOptions]:
    """build a pydantic model validating TTS options from a voice options schema"""
    return _build_tts_options_model_cached(service.name, json.dumps(voice_options, sort_keys=True, default=str))


def get_supported_audio_formats(voice_options: Dict[str, Any]):
    """list of AudioFormat natively supported by a voice (mp3 is always assumed to be supported)"""
    format_spec = voice_options.get(cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER)
    if format_spec is None:
        return [cloudlanguagetools.options.AudioFormat.mp3]
    return [cloudlanguagetools.options.AudioFormat[value] for value in format_spec.get('values', [])]
