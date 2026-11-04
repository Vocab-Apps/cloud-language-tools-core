"""CLT-AI API client.

Entry points (verbs), each takes a request model and returns a result model:
    clt.sound(SoundRequest)               -> SoundResult          text to speech
    clt.translate(TranslateRequest)       -> TranslateResult
    clt.transliterate(TransliterateRequest) -> TransliterateResult  pinyin, IPA, romaji...
    clt.transcribe(TranscribeRequest)     -> TranscribeResult     speech to text
    clt.llm(LlmRequest)                   -> LlmResult            anything else

Every verb validates its request first (clt.validate_sound(), clt.validate_translate()...): the
validation resolves defaults and checks service specific parameters (voice, options...) against
the service's pydantic models without making any API call, and returns the fully resolved
request, which can be pinned in generated code for repeatable results.

Discovery functions (no API cost): list_languages, list_audio_languages, list_voices,
describe_voice_options, list_translation_services, list_transliterations,
list_transcription_services, describe_transcription_options, list_llm_services,
describe_llm_options, describe_api.

Create a client with cloudlanguagetools.cltai.create_client(CltAPIVersion.v1).
"""

import os
import json
import uuid
import inspect
import logging
import textwrap
import tempfile
from typing import Any, Dict, List, Optional

import pydantic
import pydub

import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.options
import cloudlanguagetools.optionsmodels
import cloudlanguagetools.servicemanager
import cloudlanguagetools.encryption
from cloudlanguagetools.constants import Service, Gender
from cloudlanguagetools.languages import Language, AudioLanguage, AudioLanguageDefaults
from cloudlanguagetools.options import AudioFormat

from cloudlanguagetools.cltai import defaults
from cloudlanguagetools.cltai.types import (CltAPIVersion, CltAIError, parse_language, parse_audio_language)
from cloudlanguagetools.cltai.models import (
    SoundRequest, SoundResult, VoiceInfo,
    TranslateRequest, TranslateResult, TranslationServiceInfo,
    TransliterateRequest, TransliterateResult, TransliterationInfo,
    TranscribeRequest, TranscribeResult,
    LlmRequest, LlmResult,
    LanguageInfo, AudioLanguageInfo,
)

logger = logging.getLogger(__name__)

# keys of transliteration / voice keys which must never be shown to an LLM
SECRET_KEY_FIELDS = ['api_key']

AUDIO_FILE_EXTENSIONS = {
    AudioFormat.mp3: 'mp3',
    AudioFormat.mp3_hq: 'mp3',
    AudioFormat.ogg_opus: 'ogg',
    AudioFormat.ogg_vorbis: 'ogg',
    AudioFormat.wav: 'wav',
}

EXTENSION_AUDIO_FORMATS = {
    'mp3': AudioFormat.mp3,
    'ogg': AudioFormat.ogg_opus,
    'opus': AudioFormat.ogg_opus,
    'oga': AudioFormat.ogg_opus,
    'wav': AudioFormat.wav,
}

# formats which can be produced locally from mp3 when a voice doesn't produce them natively
PYDUB_EXPORT_PARAMETERS = {
    AudioFormat.ogg_opus: {'format': 'ogg', 'codec': 'libopus'},
    AudioFormat.ogg_vorbis: {'format': 'ogg', 'codec': 'libvorbis'},
    AudioFormat.wav: {'format': 'wav'},
}

MAX_LISTED_ALTERNATIVES = 40


def sanitize_key(key):
    if isinstance(key, dict):
        return {k: v for k, v in key.items() if k not in SECRET_KEY_FIELDS}
    return key


def _format_alternatives(values) -> str:
    values = list(values)
    text = ', '.join(str(v) for v in values[:MAX_LISTED_ALTERNATIVES])
    if len(values) > MAX_LISTED_ALTERNATIVES:
        text += f', ... ({len(values)} in total)'
    return text


def _validation_error_message(error: pydantic.ValidationError) -> str:
    return '; '.join(f"{'.'.join(str(p) for p in e['loc']) or 'request'}: {e['msg']}" for e in error.errors())


class CltAIClientV1():
    """CLT-AI API, version 1. See the module docstring for an overview."""
    api_version = CltAPIVersion.v1

    def __init__(self, manager: cloudlanguagetools.servicemanager.ServiceManager = None, output_dir: str = None):
        """manager: a configured ServiceManager (by default one is created from the encrypted backend
        configuration, encryption.load_configuration(), which requires CLOUDLANGUAGETOOLS_CORE_KEY).
        Only the services enabled in the manager's configuration are used.
        output_dir: where generated audio files are written (by default a new temporary directory)."""
        if manager is None:
            manager = cloudlanguagetools.servicemanager.ServiceManager(cloudlanguagetools.encryption.load_configuration())
        self.manager = manager
        self.output_dir = output_dir or tempfile.mkdtemp(prefix='cltai_')
        os.makedirs(self.output_dir, exist_ok=True)

    # helpers
    # =======

    def _coerce(self, request, model_class, fields):
        if request is None:
            request = fields
        elif len(fields) > 0:
            raise CltAIError(f'pass either a {model_class.__name__} or keyword arguments, not both')
        if isinstance(request, model_class):
            return request
        if isinstance(request, pydantic.BaseModel):
            raise CltAIError(f'expected {model_class.__name__}, got {type(request).__name__}')
        try:
            return model_class.model_validate(request)
        except pydantic.ValidationError as e:
            raise CltAIError(f'invalid {model_class.__name__}: {_validation_error_message(e)}') from e

    def _get_service(self, service: Service):
        if service not in self.manager.services:
            raise CltAIError(f'service {service.name} is not enabled, enabled services: {_format_alternatives(s.name for s in self.manager.services)}')
        return self.manager.services[service]

    def _validate_options(self, options_model, options: Dict[str, Any], context: str) -> Dict[str, Any]:
        try:
            return options_model(**options).to_service_options()
        except pydantic.ValidationError as e:
            schema = json.dumps(options_model.model_json_schema().get('properties', {}))
            raise CltAIError(f'invalid options for {context}: {_validation_error_message(e)}. Valid options: {schema}') from e

    # discovery: languages
    # ====================

    def list_languages(self) -> List[LanguageInfo]:
        """all language codes accepted in `language` / `source_language` / `target_language` fields"""
        return [LanguageInfo(code=language.name, name=language.lang_name) for language in Language]

    def list_audio_languages(self, language: str = None) -> List[AudioLanguageInfo]:
        """locale codes accepted in `audio_language`, optionally restricted to one language"""
        language_enum = parse_language(language) if language is not None else None
        return [AudioLanguageInfo(code=audio_language.name, name=audio_language.audio_lang_name, language=audio_language.lang.name)
                for audio_language in AudioLanguage
                if language_enum is None or audio_language.lang == language_enum]

    # sound
    # =====

    def _get_voices(self):
        try:
            return self.manager.get_tts_voice_list_v3()
        except Exception:
            logger.exception('could not retrieve full voice list, retrieving per service')
            result = []
            for service_enum, service in self.manager.services.items():
                try:
                    result.extend(service.get_tts_voice_list_v3())
                except Exception:
                    logger.exception(f'could not retrieve voice list for {service_enum.name}')
            return result

    def _voice_info(self, voice) -> VoiceInfo:
        return VoiceInfo(
            service=voice.service,
            name=voice.name,
            voice_key=sanitize_key(voice.voice_key),
            gender=voice.gender,
            audio_languages=voice.audio_languages,
            service_fee=voice.service_fee,
            options={k: v for k, v in voice.options.items() if k != cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER},
            formats=cloudlanguagetools.optionsmodels.get_supported_audio_formats(voice.options))

    def _filter_voices(self, voices, language=None, audio_language=None, service=None, gender=None, name_contains=None):
        if audio_language is not None:
            voices = [v for v in voices if audio_language in v.audio_languages]
        elif language is not None:
            voices = [v for v in voices if any(al.lang == language for al in v.audio_languages)]
        if service is not None:
            voices = [v for v in voices if v.service == service]
        if gender is not None:
            voices = [v for v in voices if v.gender == gender]
        if name_contains is not None:
            voices = [v for v in voices if name_contains.lower() in v.name.lower()]
        return voices

    def list_voices(self, language: str = None, audio_language: str = None, service: str = None,
            gender: str = None, name_contains: str = None) -> List[VoiceInfo]:
        """TTS voices, filtered by language code (e.g. "fr"), locale (e.g. "fr_CA"), service (e.g. "Azure"),
        gender ("Male" / "Female") and case-insensitive substring of the voice name"""
        voices = self._filter_voices(self._get_voices(),
            language=parse_language(language) if language is not None else None,
            audio_language=parse_audio_language(audio_language) if audio_language is not None else None,
            service=Service(service) if service is not None else None,
            gender=Gender(gender) if gender is not None else None,
            name_contains=name_contains)
        return [self._voice_info(v) for v in voices]

    def _find_voice(self, request: SoundRequest):
        language = request.language
        if request.audio_language is not None and request.audio_language.lang != language:
            raise CltAIError(f'audio_language {request.audio_language.name} is not a locale of language {language.name}, '
                             f'valid locales: {_format_alternatives(a.name for a in AudioLanguage if a.lang == language)}')
        default_audio_language = request.audio_language or AudioLanguageDefaults.get(language)

        candidates = self._filter_voices(self._get_voices(), language=language, audio_language=request.audio_language)
        if len(candidates) == 0:
            raise CltAIError(f'no voice found for language {language.name}' +
                (f' / audio_language {request.audio_language.name}' if request.audio_language else ''))

        if request.service is not None:
            self._get_service(request.service)
            service_voices = [v for v in candidates if v.service == request.service]
            if len(service_voices) == 0:
                raise CltAIError(f'service {request.service.name} has no voice for {(request.audio_language or language).name}, '
                                 f'services with voices: {_format_alternatives(sorted(set(v.service.name for v in candidates)))}')
            candidates = service_voices

        if request.voice_key is not None:
            requested_key = sanitize_key(request.voice_key)
            matches = [v for v in candidates if sanitize_key(v.voice_key) == requested_key]
            if len(matches) == 0:
                raise CltAIError(f'voice_key {request.voice_key} not found for {request.service.name} / {language.name}. '
                                 f'Use clt.list_voices(language="{language.name}", service="{request.service.name}") to find valid voices')
            return matches[0], default_audio_language

        if request.voice_name is not None:
            matches = [v for v in candidates if v.name == request.voice_name]
            if len(matches) == 0:
                matches = [v for v in candidates if v.name.lower() == request.voice_name.lower()]
            if len(matches) == 0:
                raise CltAIError(f'voice_name "{request.voice_name}" not found for {request.service.name} / {language.name}, '
                                 f'valid voice names: {_format_alternatives(v.name for v in candidates)}')
            if request.gender is not None and matches[0].gender != request.gender:
                raise CltAIError(f'voice {request.voice_name} is {matches[0].gender.name}, not {request.gender.name}')
            return matches[0], default_audio_language

        if request.gender is not None:
            gender_candidates = [v for v in candidates if v.gender == request.gender]
            if len(gender_candidates) == 0:
                raise CltAIError(f'no {request.gender.name} voice found for {language.name}' +
                    (f' with {request.service.name}' if request.service else '') +
                    f', available genders: {_format_alternatives(sorted(set(v.gender.name for v in candidates)))}')
            candidates = gender_candidates

        # select service
        services = defaults.order_by_preference([v.service for v in candidates], defaults.SOUND_SERVICE_PREFERENCE)
        candidates = [v for v in candidates if v.service == services[0]]

        # select gender
        available_genders = set(v.gender for v in candidates)
        gender = [g for g in defaults.SOUND_GENDER_PREFERENCE if g in available_genders][0]
        candidates = [v for v in candidates if v.gender == gender]

        # prefer voices native to the default locale, then single language voices (stable sort keeps service ordering)
        def voice_rank(voice):
            return (
                0 if default_audio_language in voice.audio_languages else 1,
                0 if len(voice.audio_languages) == 1 else 1,
            )
        candidates = sorted(candidates, key=voice_rank)
        return candidates[0], default_audio_language

    def _resolve_sound(self, request: SoundRequest):
        voice, default_audio_language = self._find_voice(request)
        service = self._get_service(voice.service)

        if request.audio_language is not None:
            audio_language = request.audio_language
        elif default_audio_language in voice.audio_languages:
            audio_language = default_audio_language
        else:
            audio_language = [a for a in voice.audio_languages if a.lang == request.language][0]

        options = self._validate_options(service.get_tts_options_model(voice), request.options,
            f'{voice.service.name} voice {voice.name}')

        native_formats = cloudlanguagetools.optionsmodels.get_supported_audio_formats(voice.options)
        if request.format not in native_formats and request.format not in PYDUB_EXPORT_PARAMETERS:
            raise CltAIError(f'format {request.format.name} is not supported by {voice.service.name} voice {voice.name}, '
                             f'supported formats: {_format_alternatives(f.name for f in native_formats + list(PYDUB_EXPORT_PARAMETERS))}')

        resolved = request.model_copy(update={
            'audio_language': audio_language,
            'service': voice.service,
            'voice_name': voice.name,
            'voice_key': sanitize_key(voice.voice_key),
            'options': options,
        })
        return resolved, voice, native_formats

    def validate_sound(self, request: SoundRequest = None, **fields) -> SoundRequest:
        """validate a sound request without generating audio, returns the fully resolved request
        (service, voice and options filled in). Raises CltAIError if the request is invalid."""
        request = self._coerce(request, SoundRequest, fields)
        resolved, voice, native_formats = self._resolve_sound(request)
        return resolved

    def describe_voice_options(self, service: str, voice_name: str = None, voice_key: Dict[str, Any] = None) -> Dict[str, Any]:
        """JSON schema of the `options` accepted by a voice (pass voice_name or voice_key from list_voices)"""
        service_enum = Service(service)
        voices = [v for v in self._get_voices() if v.service == service_enum]
        if voice_key is not None:
            voices = [v for v in voices if sanitize_key(v.voice_key) == sanitize_key(voice_key)]
        elif voice_name is not None:
            voices = [v for v in voices if v.name.lower() == voice_name.lower()]
        if len(voices) == 0:
            raise CltAIError(f'voice not found for {service}: voice_name={voice_name} voice_key={voice_key}')
        return self._get_service(service_enum).get_tts_options_model(voices[0]).model_json_schema()

    def sound(self, request: SoundRequest = None, **fields) -> SoundResult:
        """generate audio for some text. Returns a SoundResult, the audio file is SoundResult.audio_path"""
        request = self._coerce(request, SoundRequest, fields)
        resolved, voice, native_formats = self._resolve_sound(request)

        options = dict(resolved.options)
        convert = False
        if cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER in voice.options and resolved.format in native_formats:
            options[cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER] = resolved.format.name
        elif resolved.format != AudioFormat.mp3:
            # the service produces mp3, convert locally
            convert = True

        logger.info(f'cltai sound: {resolved.service.name} voice {voice.name} options {options}')
        audio_temp_file = self.manager.get_tts_audio(resolved.text, voice.service.name, voice.voice_key, options)

        output_path = os.path.join(self.output_dir, f'clt_sound_{uuid.uuid4().hex}.{AUDIO_FILE_EXTENSIONS[resolved.format]}')
        if convert:
            audio = pydub.AudioSegment.from_mp3(audio_temp_file.name)
            audio.export(output_path, **PYDUB_EXPORT_PARAMETERS[resolved.format])
        else:
            with open(audio_temp_file.name, 'rb') as source, open(output_path, 'wb') as destination:
                destination.write(source.read())

        return SoundResult(
            audio_path=output_path,
            format=resolved.format,
            text=resolved.text,
            service=resolved.service,
            voice_name=resolved.voice_name,
            voice_key=resolved.voice_key,
            audio_language=resolved.audio_language,
            options=resolved.options)

    # translate
    # =========

    def _translation_services(self, source_language: Language, target_language: Language) -> List[TranslationServiceInfo]:
        translation_list = self.manager.get_translation_language_list()
        source_entries = {}
        target_entries = {}
        for entry in translation_list:
            if entry.language == source_language:
                source_entries.setdefault(entry.service, entry)
            if entry.language == target_language:
                target_entries.setdefault(entry.service, entry)
        services = defaults.order_by_preference(
            [s for s in source_entries if s in target_entries], defaults.TRANSLATION_SERVICE_PREFERENCE)
        return [TranslationServiceInfo(
            service=service,
            source_language=source_language,
            target_language=target_language,
            source_language_id=source_entries[service].get_language_id(),
            target_language_id=target_entries[service].get_language_id(),
            service_fee=source_entries[service].service_fee) for service in services]

    def list_translation_services(self, source_language: str, target_language: str) -> List[TranslationServiceInfo]:
        """services able to translate from source_language to target_language, in order of preference"""
        return self._translation_services(parse_language(source_language), parse_language(target_language))

    def _resolve_translate(self, request: TranslateRequest):
        if request.source_language == request.target_language:
            raise CltAIError(f'source_language and target_language are both {request.source_language.name}')
        services = self._translation_services(request.source_language, request.target_language)
        if len(services) == 0:
            raise CltAIError(f'no translation service found from {request.source_language.name} to {request.target_language.name}')
        if request.service is not None:
            matches = [s for s in services if s.service == request.service]
            if len(matches) == 0:
                raise CltAIError(f'{request.service.name} cannot translate from {request.source_language.name} to {request.target_language.name}, '
                                 f'services which can: {_format_alternatives(s.service.name for s in services)}')
            selected = matches[0]
        else:
            selected = services[0]
        return request.model_copy(update={'service': selected.service}), selected

    def validate_translate(self, request: TranslateRequest = None, **fields) -> TranslateRequest:
        """validate a translation request without translating, returns the resolved request"""
        request = self._coerce(request, TranslateRequest, fields)
        return self._resolve_translate(request)[0]

    def translate(self, request: TranslateRequest = None, **fields) -> TranslateResult:
        """translate text from source_language to target_language"""
        request = self._coerce(request, TranslateRequest, fields)
        resolved, selected = self._resolve_translate(request)
        translated_text = self.manager.get_translation(resolved.text, selected.service.name,
            selected.source_language_id, selected.target_language_id)
        return TranslateResult(text=translated_text, source_text=resolved.text,
            source_language=resolved.source_language, target_language=resolved.target_language,
            service=selected.service)

    # transliterate
    # =============

    def _transliteration_options(self, language: Language = None, service: Service = None, name_contains: str = None):
        options = self.manager.get_transliteration_language_list()
        if language is not None:
            options = [o for o in options if o.language == language]
        if service is not None:
            options = [o for o in options if o.service == service]
        if name_contains is not None:
            options = [o for o in options if name_contains.lower() in o.get_transliteration_name().lower()]
        return options

    def _transliteration_info(self, option) -> TransliterationInfo:
        return TransliterationInfo(service=option.service, language=option.language,
            name=option.get_transliteration_name(), key=sanitize_key(option.get_transliteration_key()),
            service_fee=option.service_fee)

    def list_transliterations(self, language: str = None, service: str = None, name_contains: str = None) -> List[TransliterationInfo]:
        """transliteration options (pinyin, jyutping, IPA, romaji...), filtered by language code, service,
        and case-insensitive substring of the name"""
        options = self._transliteration_options(
            language=parse_language(language) if language is not None else None,
            service=Service(service) if service is not None else None,
            name_contains=name_contains)
        return [self._transliteration_info(o) for o in options]

    def _resolve_transliterate(self, request: TransliterateRequest):
        language = request.language
        all_options = self._transliteration_options(language=language)
        if len(all_options) == 0:
            raise CltAIError(f'no transliteration available for {language.name}')
        candidates = all_options
        if request.service is not None:
            candidates = [o for o in candidates if o.service == request.service]
            if len(candidates) == 0:
                raise CltAIError(f'{request.service.name} has no transliteration for {language.name}, '
                                 f'services which do: {_format_alternatives(sorted(set(o.service.name for o in all_options)))}')
        if request.transliteration_key is not None:
            requested_key = sanitize_key(request.transliteration_key)
            candidates = [o for o in candidates if sanitize_key(o.get_transliteration_key()) == requested_key]
            if len(candidates) == 0:
                raise CltAIError(f'transliteration_key {request.transliteration_key} not found, '
                                 f'use clt.list_transliterations(language="{language.name}") to find valid keys')
        if request.transliteration_name is not None:
            name_candidates = [o for o in candidates if request.transliteration_name.lower() in o.get_transliteration_name().lower()]
            if len(name_candidates) == 0:
                raise CltAIError(f'no transliteration named like "{request.transliteration_name}" for {language.name}, '
                                 f'available: {_format_alternatives(o.get_transliteration_name() for o in candidates)}')
            candidates = name_candidates

        services = defaults.order_by_preference([o.service for o in candidates], defaults.TRANSLITERATION_SERVICE_PREFERENCE)
        candidates = [o for o in candidates if o.service == services[0]]
        if language in defaults.CHINESE_LANGUAGES and services[0] == Service.MandarinCantonese:
            def chinese_rank(option):
                key = option.get_transliteration_key()
                return sum(0 if key.get(k) == v else 1 for k, v in defaults.CHINESE_TRANSLITERATION_DEFAULT_KEY.items())
            candidates = sorted(candidates, key=chinese_rank)
        selected = candidates[0]
        resolved = request.model_copy(update={
            'service': selected.service,
            'transliteration_name': selected.get_transliteration_name(),
            'transliteration_key': sanitize_key(selected.get_transliteration_key()),
        })
        return resolved, selected

    def validate_transliterate(self, request: TransliterateRequest = None, **fields) -> TransliterateRequest:
        """validate a transliteration request, returns the resolved request"""
        request = self._coerce(request, TransliterateRequest, fields)
        return self._resolve_transliterate(request)[0]

    def transliterate(self, request: TransliterateRequest = None, **fields) -> TransliterateResult:
        """convert text into pinyin, jyutping, IPA, romaji or another romanization"""
        request = self._coerce(request, TransliterateRequest, fields)
        resolved, selected = self._resolve_transliterate(request)
        text = self.manager.get_transliteration(resolved.text, selected.service.name, selected.get_transliteration_key())
        return TransliterateResult(text=text, source_text=resolved.text, language=resolved.language,
            service=selected.service, transliteration_name=resolved.transliteration_name,
            transliteration_key=resolved.transliteration_key)

    # transcribe
    # ==========

    def list_transcription_services(self) -> List[Service]:
        """services able to transcribe audio, in order of preference"""
        return defaults.order_by_preference(self.manager.get_transcription_services(), defaults.TRANSCRIPTION_SERVICE_PREFERENCE)

    def describe_transcription_options(self, service: str) -> Dict[str, Any]:
        """JSON schema of the `options` accepted by a transcription service"""
        model = self._get_service(Service(service)).get_transcription_options_model()
        if model is None:
            raise CltAIError(f'{service} does not support transcription')
        return model.model_json_schema()

    def _resolve_transcribe(self, request: TranscribeRequest):
        services = self.list_transcription_services()
        if len(services) == 0:
            raise CltAIError('no transcription service available')
        if request.service is not None:
            if request.service not in services:
                raise CltAIError(f'{request.service.name} does not support transcription, services which do: {_format_alternatives(s.name for s in services)}')
            service = request.service
        else:
            service = services[0]
        audio_format = request.format
        if audio_format is None:
            extension = os.path.splitext(request.audio_path)[1].lstrip('.').lower()
            if extension not in EXTENSION_AUDIO_FORMATS:
                raise CltAIError(f'cannot guess audio format from file name {request.audio_path}, set `format`')
            audio_format = EXTENSION_AUDIO_FORMATS[extension]
        options = self._validate_options(self._get_service(service).get_transcription_options_model(),
            request.options, f'{service.name} transcription')
        return request.model_copy(update={'service': service, 'format': audio_format, 'options': options})

    def validate_transcribe(self, request: TranscribeRequest = None, **fields) -> TranscribeRequest:
        """validate a transcription request, returns the resolved request"""
        request = self._coerce(request, TranscribeRequest, fields)
        return self._resolve_transcribe(request)

    def transcribe(self, request: TranscribeRequest = None, **fields) -> TranscribeResult:
        """convert audio into text. Generated audio can be passed directly: clt.transcribe(audio=sound_result)"""
        request = self._coerce(request, TranscribeRequest, fields)
        resolved = self._resolve_transcribe(request)
        text = self.manager.get_transcription(resolved.audio_path, resolved.service.name, resolved.format,
            resolved.language, resolved.options)
        return TranscribeResult(text=text, language=resolved.language, service=resolved.service)

    # llm
    # ===

    def list_llm_services(self) -> List[Service]:
        """services able to answer llm prompts, in order of preference"""
        return defaults.order_by_preference(self.manager.get_llm_services(), defaults.LLM_SERVICE_PREFERENCE)

    def describe_llm_options(self, service: str) -> Dict[str, Any]:
        """JSON schema of the `options` accepted by an llm service (model...)"""
        model = self._get_service(Service(service)).get_llm_options_model()
        if model is None:
            raise CltAIError(f'{service} does not support llm')
        return model.model_json_schema()

    def _resolve_llm(self, request: LlmRequest):
        services = self.list_llm_services()
        if len(services) == 0:
            raise CltAIError('no llm service available')
        if request.service is not None:
            if request.service not in services:
                raise CltAIError(f'{request.service.name} does not support llm, services which do: {_format_alternatives(s.name for s in services)}')
            service = request.service
        else:
            service = services[0]
        options = self._validate_options(self._get_service(service).get_llm_options_model(),
            request.options, f'{service.name} llm')
        return request.model_copy(update={'service': service, 'options': options})

    def validate_llm(self, request: LlmRequest = None, **fields) -> LlmRequest:
        """validate an llm request, returns the resolved request"""
        request = self._coerce(request, LlmRequest, fields)
        return self._resolve_llm(request)

    def llm(self, request: LlmRequest = None, **fields) -> LlmResult:
        """answer a question / generate text with an LLM. Use only when the other verbs can't do the job"""
        request = self._coerce(request, LlmRequest, fields)
        resolved = self._resolve_llm(request)
        text = self.manager.get_llm_response(resolved.prompt, resolved.service.name, resolved.instructions, resolved.options)
        return LlmResult(text=text, service=resolved.service, options=resolved.options)

    # generic validation
    # ==================

    def validate(self, request: pydantic.BaseModel) -> pydantic.BaseModel:
        """validate any request model, returns the resolved request"""
        validators = {
            SoundRequest: self.validate_sound,
            TranslateRequest: self.validate_translate,
            TransliterateRequest: self.validate_transliterate,
            TranscribeRequest: self.validate_transcribe,
            LlmRequest: self.validate_llm,
        }
        if type(request) not in validators:
            raise CltAIError(f'not a CLT-AI request: {type(request).__name__}')
        return validators[type(request)](request)

    # self description
    # ================

    VERBS = ['sound', 'translate', 'transliterate', 'transcribe', 'llm']
    DISCOVERY_FUNCTIONS = ['list_languages', 'list_audio_languages', 'list_voices', 'describe_voice_options',
        'list_translation_services', 'list_transliterations', 'list_transcription_services',
        'describe_transcription_options', 'list_llm_services', 'describe_llm_options']
    VALIDATION_FUNCTIONS = ['validate_sound', 'validate_translate', 'validate_transliterate', 'validate_transcribe', 'validate_llm']
    REQUEST_MODELS = [SoundRequest, TranslateRequest, TransliterateRequest, TranscribeRequest, LlmRequest]
    RESULT_MODELS = [SoundResult, TranslateResult, TransliterateResult, TranscribeResult, LlmResult]

    def describe_api(self) -> str:
        """text description of the API: function signatures, docstrings and model schemas"""
        def short_signature(method):
            signature = str(inspect.signature(method))
            for prefix in ['cloudlanguagetools.cltai.models.', 'cloudlanguagetools.constants.']:
                signature = signature.replace(prefix, '')
            return signature

        def describe_functions(names):
            lines = []
            for name in names:
                method = getattr(self, name)
                lines.append(f'clt.{name}{short_signature(method)}')
                lines.append(textwrap.indent(inspect.getdoc(method), '    '))
            return '\n'.join(lines)

        def describe_models(models):
            lines = []
            for model in models:
                docstring = inspect.cleandoc(model.__dict__.get('__doc__') or '')
                lines.append(f"{model.__name__}: {' '.join(docstring.split())}")
                schema = model.model_json_schema()
                for field_name, field_schema in schema.get('properties', {}).items():
                    required = field_name in schema.get('required', [])
                    field_type = field_schema.get('type') or ' | '.join(
                        s.get('type', s.get('$ref', '').split('/')[-1]) for s in field_schema.get('anyOf', [])) or field_schema.get('$ref', '').split('/')[-1]
                    if 'enum' in field_schema:
                        field_type = 'one of ' + ', '.join(str(v) for v in field_schema['enum'])
                    description = field_schema.get('description', '')
                    lines.append(f"    {field_name}: {field_type}{' (required)' if required else ''}  {description}")
            return '\n'.join(lines)

        return f"""CLT-AI API {self.api_version.value}
import: from cloudlanguagetools.cltai import {', '.join(m.__name__ for m in self.REQUEST_MODELS)}, CltAIError
`clt` is a client created with cloudlanguagetools.cltai.create_client(CltAPIVersion.{self.api_version.value})
Verbs also accept keyword arguments, e.g. clt.translate(text='hello', source_language='en', target_language='fr').
Invalid requests raise CltAIError with an explanation and valid alternatives.
Service names: {', '.join(s.name for s in self.manager.services)}

== verbs (make API calls) ==
{describe_functions(self.VERBS)}

== validation (no API call, returns the fully resolved request) ==
{describe_functions(self.VALIDATION_FUNCTIONS)}

== discovery (no API call cost) ==
{describe_functions(self.DISCOVERY_FUNCTIONS)}

== request models ==
{describe_models(self.REQUEST_MODELS)}

== result models ==
{describe_models(self.RESULT_MODELS)}
"""


CLIENT_CLASSES = {
    CltAPIVersion.v1: CltAIClientV1,
}


def create_client(version: CltAPIVersion, manager: cloudlanguagetools.servicemanager.ServiceManager = None,
        output_dir: str = None) -> CltAIClientV1:
    """create a CLT-AI API client for the given API version"""
    version = CltAPIVersion(version)
    return CLIENT_CLASSES[version](manager=manager, output_dir=output_dir)
