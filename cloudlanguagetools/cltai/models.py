"""Pydantic models for CLT-AI API v1: one request and one result model per verb, plus the
models returned by the discovery functions.

Every request model rejects unknown fields. Fields left as None are filled in by the default
selection rules (see cloudlanguagetools.cltai.defaults), and the result reports what was
actually used, so a choice made once can be pinned in generated code.
"""

import os
from typing import Any, Dict, List, Optional

import pydantic
from pydantic import Field

from cloudlanguagetools.constants import Service, Gender, ServiceFee
from cloudlanguagetools.options import AudioFormat
from cloudlanguagetools.cltai.types import LanguageCode, AudioLanguageCode, AudioFormatCode


class CltModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra='forbid')


# sound (text to speech)
# ======================

class SoundRequest(CltModel):
    """generate audio (text to speech) for some text"""
    text: str = Field(min_length=1, description='text to pronounce')
    language: LanguageCode = Field(description='language of the text')
    audio_language: Optional[AudioLanguageCode] = Field(default=None,
        description='specific locale/accent, e.g. en_GB vs en_US. Defaults to the main locale of `language`')
    service: Optional[Service] = Field(default=None, description='TTS service, e.g. Azure, Google, Amazon, OpenAI, ElevenLabs')
    voice_name: Optional[str] = Field(default=None,
        description='voice name exactly as returned by clt.list_voices() (VoiceInfo.name), requires `service`')
    voice_key: Optional[Dict[str, Any]] = Field(default=None,
        description='exact voice key as returned by clt.list_voices() (VoiceInfo.voice_key), requires `service`. '
                    'Most precise way to pin a voice, takes precedence over voice_name')
    gender: Optional[Gender] = Field(default=None, description='preferred voice gender when no voice is specified')
    options: Dict[str, Any] = Field(default_factory=dict,
        description='voice specific options (speed, pitch, style, model...). Valid options depend on the voice: '
                    'see VoiceInfo.options or clt.describe_voice_options()')
    format: AudioFormatCode = Field(default=AudioFormat.mp3, description='output audio format')

    @pydantic.model_validator(mode='after')
    def check_voice_requires_service(self):
        if (self.voice_name is not None or self.voice_key is not None) and self.service is None:
            raise ValueError('`service` must be specified together with voice_name / voice_key')
        return self


class VoiceInfo(CltModel):
    """a TTS voice, as returned by clt.list_voices()"""
    service: Service
    name: str
    voice_key: Dict[str, Any]
    gender: Gender
    audio_languages: List[AudioLanguageCode] = Field(description='locales this voice can speak, multilingual voices have several')
    service_fee: ServiceFee
    options: Dict[str, Any] = Field(description='schema of the options accepted by this voice (type, min, max, values, default)')
    formats: List[AudioFormatCode] = Field(description='audio formats the service produces natively for this voice')


class SoundResult(CltModel):
    """generated audio file, along with the voice which was actually used"""
    audio_path: str = Field(description='path of the generated audio file')
    format: AudioFormatCode
    text: str
    service: Service
    voice_name: str
    voice_key: Dict[str, Any]
    audio_language: AudioLanguageCode
    options: Dict[str, Any]

    def read_bytes(self) -> bytes:
        with open(self.audio_path, 'rb') as f:
            return f.read()

    def save(self, path: str) -> str:
        """copy the audio file to `path`, returns path"""
        with open(path, 'wb') as f:
            f.write(self.read_bytes())
        return path


# translate
# =========

class TranslateRequest(CltModel):
    """translate text from one language to another"""
    text: str = Field(min_length=1, description='text to translate')
    source_language: LanguageCode = Field(description='language of the text')
    target_language: LanguageCode = Field(description='language to translate into')
    service: Optional[Service] = Field(default=None, description='translation service, e.g. DeepL, Azure, Google, Amazon')


class TranslationServiceInfo(CltModel):
    """a translation service able to translate between two languages, as returned by clt.list_translation_services()"""
    service: Service
    source_language: LanguageCode
    target_language: LanguageCode
    source_language_id: str
    target_language_id: str
    service_fee: ServiceFee


class TranslateResult(CltModel):
    """result of clt.translate()"""
    text: str = Field(description='translated text')
    source_text: str
    source_language: LanguageCode
    target_language: LanguageCode
    service: Service


# transliterate
# =============

class TransliterateRequest(CltModel):
    """convert text into another script or notation: pinyin, jyutping, romaji, IPA, romanization..."""
    text: str = Field(min_length=1, description='text to transliterate')
    language: LanguageCode = Field(description='language of the text')
    service: Optional[Service] = Field(default=None, description='transliteration service')
    transliteration_name: Optional[str] = Field(default=None,
        description='selects the transliteration by name, case-insensitive substring of TransliterationInfo.name, '
                    'e.g. "pinyin", "ipa", "romaji", "jyutping", "tone numbers"')
    transliteration_key: Optional[Dict[str, Any] | str] = Field(default=None,
        description='exact key as returned by clt.list_transliterations() (TransliterationInfo.key), requires `service`. '
                    'Most precise way to pin a transliteration')

    @pydantic.model_validator(mode='after')
    def check_key_requires_service(self):
        if self.transliteration_key is not None and self.service is None:
            raise ValueError('`service` must be specified together with transliteration_key')
        return self


class TransliterationInfo(CltModel):
    """a transliteration option, as returned by clt.list_transliterations()"""
    service: Service
    language: LanguageCode
    name: str
    key: Dict[str, Any] | str
    service_fee: ServiceFee


class TransliterateResult(CltModel):
    """result of clt.transliterate()"""
    text: str = Field(description='transliterated text')
    source_text: str
    language: LanguageCode
    service: Service
    transliteration_name: str
    transliteration_key: Dict[str, Any] | str


# transcribe (speech to text)
# ===========================

class TranscribeRequest(CltModel):
    """convert audio into text (speech recognition)"""
    audio_path: str = Field(description='path of the audio file to transcribe. A SoundResult can be passed as `audio`')
    format: Optional[AudioFormatCode] = Field(default=None,
        description='format of the audio file, guessed from the file extension when not set')
    language: Optional[LanguageCode] = Field(default=None, description='language spoken in the audio, improves accuracy')
    service: Optional[Service] = Field(default=None, description='transcription service, e.g. OpenAI, Azure')
    options: Dict[str, Any] = Field(default_factory=dict,
        description='service specific options, see clt.describe_transcription_options()')

    @pydantic.model_validator(mode='before')
    @classmethod
    def accept_sound_result(cls, data):
        # TranscribeRequest(audio=sound_result) is a convenient way to transcribe generated audio
        if isinstance(data, dict) and 'audio' in data:
            data = dict(data)
            audio = data.pop('audio')
            if isinstance(audio, SoundResult):
                data.setdefault('audio_path', audio.audio_path)
                data.setdefault('format', audio.format)
                data.setdefault('language', audio.audio_language.lang)
            else:
                data.setdefault('audio_path', str(audio))
        return data

    @pydantic.field_validator('audio_path')
    @classmethod
    def check_file_exists(cls, value):
        if not os.path.isfile(value):
            raise ValueError(f'audio file not found: {value}')
        return value


class TranscribeResult(CltModel):
    """result of clt.transcribe()"""
    text: str = Field(description='transcribed text')
    language: Optional[LanguageCode]
    service: Service


# llm
# ===

class LlmRequest(CltModel):
    """answer a question or generate text with a large language model, for anything which can't be done
    with sound / translate / transliterate / transcribe (explanations, example sentences, grammar notes...)"""
    prompt: str = Field(min_length=1, description='the question or instruction, including the input text')
    instructions: Optional[str] = Field(default=None,
        description='optional system instructions, e.g. output format constraints ("answer with a single sentence, no markdown")')
    service: Optional[Service] = Field(default=None, description='llm service, e.g. OpenAI')
    options: Dict[str, Any] = Field(default_factory=dict,
        description='service specific options such as model, see clt.describe_llm_options()')


class LlmResult(CltModel):
    """result of clt.llm()"""
    text: str = Field(description='generated text')
    service: Service
    options: Dict[str, Any]


# other discovery models
# ======================

class LanguageInfo(CltModel):
    """a language code, as returned by clt.list_languages()"""
    code: str
    name: str


class AudioLanguageInfo(CltModel):
    """a locale code, as returned by clt.list_audio_languages()"""
    code: str
    name: str
    language: str
