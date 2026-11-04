"""Shared types for the CLT-AI API: versions, errors, and enum types that (de)serialize by code.

Languages, audio languages and audio formats are exchanged as short codes ("fr", "zh_cn",
"fr_FR", "mp3") rather than enum values, which keeps them readable for LLMs and in generated code.
"""

import enum
from typing import Annotated

import pydantic

import cloudlanguagetools.errors
import cloudlanguagetools.languages
import cloudlanguagetools.options


class CltAPIVersion(enum.StrEnum):
    """versions of the CLT-AI API. A new version is added when the contract changes; older
    versions keep working unchanged. Pass the version when creating a client."""
    v1 = 'v1'

LATEST_VERSION = CltAPIVersion.v1


class CltAIError(cloudlanguagetools.errors.InputError):
    """invalid CLT-AI request: the message explains what is wrong and lists valid alternatives"""
    pass


def _normalize(code: str) -> str:
    return code.strip().replace('-', '_')


def _enum_by_code(enum_class, value, kind: str):
    if isinstance(value, enum_class):
        return value
    if not isinstance(value, str):
        raise ValueError(f'{kind} must be a string code, got {value!r}')
    code = _normalize(value)
    if code in enum_class.__members__:
        return enum_class[code]
    lower_map = {name.lower(): member for name, member in enum_class.__members__.items()}
    if code.lower() in lower_map:
        return lower_map[code.lower()]
    # 'as' is a python keyword, stored as 'as_' in the enum
    if f'{code.lower()}_' in lower_map:
        return lower_map[f'{code.lower()}_']
    raise ValueError(f'unknown {kind} code {value!r}')


def parse_language(value) -> cloudlanguagetools.languages.Language:
    if isinstance(value, str):
        # also accept full language names such as "French" or "Chinese (Simplified)"
        for language in cloudlanguagetools.languages.Language:
            if language.lang_name.lower() == value.strip().lower():
                return language
    return _enum_by_code(cloudlanguagetools.languages.Language, value, 'language')


def parse_audio_language(value) -> cloudlanguagetools.languages.AudioLanguage:
    return _enum_by_code(cloudlanguagetools.languages.AudioLanguage, value, 'audio language')


def parse_audio_format(value) -> cloudlanguagetools.options.AudioFormat:
    return _enum_by_code(cloudlanguagetools.options.AudioFormat, value, 'audio format')


LanguageCode = Annotated[
    cloudlanguagetools.languages.Language,
    pydantic.BeforeValidator(parse_language),
    pydantic.PlainSerializer(lambda language: language.name, return_type=str),
    pydantic.WithJsonSchema({'type': 'string', 'description':
        'language code, e.g. "en", "fr", "ja", "zh_cn" (Mandarin, simplified), "zh_tw" (Mandarin, traditional), "yue" (Cantonese). '
        'Use clt.list_languages() for the full list'}),
]

AudioLanguageCode = Annotated[
    cloudlanguagetools.languages.AudioLanguage,
    pydantic.BeforeValidator(parse_audio_language),
    pydantic.PlainSerializer(lambda audio_language: audio_language.name, return_type=str),
    pydantic.WithJsonSchema({'type': 'string', 'description':
        'language + region (locale/accent) code, e.g. "en_US", "en_GB", "fr_FR", "fr_CA", "zh_CN", "ja_JP"'}),
]

AudioFormatCode = Annotated[
    cloudlanguagetools.options.AudioFormat,
    pydantic.BeforeValidator(parse_audio_format),
    pydantic.PlainSerializer(lambda audio_format: audio_format.name, return_type=str),
    pydantic.WithJsonSchema({'type': 'string', 'enum': [f.name for f in cloudlanguagetools.options.AudioFormat],
        'description': 'audio file format'}),
]
