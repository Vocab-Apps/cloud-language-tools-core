import json
import pprint
import requests
import tempfile
import os
import contextlib
import logging
import urllib.parse
from typing import List

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.options
import cloudlanguagetools.languages
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.translationlanguage
import cloudlanguagetools.transliterationlanguage
import cloudlanguagetools.errors
from cloudlanguagetools.options import AudioFormat

logger = logging.getLogger(__name__)


DEFAULT_STABILITY = 0.75
DEFAULT_SIMILARITY_BOOST = 0.75

GENDER_MAP = {
    'male': cloudlanguagetools.constants.Gender.Male,
    'female': cloudlanguagetools.constants.Gender.Female,
}

VOICE_OPTIONS = {
            'stability' : {
                'type': cloudlanguagetools.options.ParameterType.number.name,
                'min': 0.0,
                'max': 1.0,
                'default': DEFAULT_STABILITY
            },
            'similarity_boost' : {
                'type': cloudlanguagetools.options.ParameterType.number.name,
                'min': 0.0,
                'max': 1.0,
                'default': DEFAULT_SIMILARITY_BOOST
            },
            cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER: {
                'type': cloudlanguagetools.options.ParameterType.list.name,
                'values': [
                    cloudlanguagetools.options.AudioFormat.mp3.name,
                    cloudlanguagetools.options.AudioFormat.wav.name
                ],
                'default': cloudlanguagetools.options.AudioFormat.mp3.name
            }
}

class ElevenLabsVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, voice_data, language: cloudlanguagetools.languages.AudioLanguage, model_id, model_short_name):
        # pprint.pprint(voice_data)
        self.service = cloudlanguagetools.constants.Service.ElevenLabs
        self.service_fee = cloudlanguagetools.constants.ServiceFee.paid
        self.voice_id = voice_data['voice_id']
        self.model_id = model_id
        self.model_short_name = model_short_name
        self.name = voice_data['name']
        self.gender = GENDER_MAP.get(voice_data['labels']['gender'], cloudlanguagetools.constants.Gender.Male)
        self.audio_language = language

    def get_voice_key(self):
        return {
            'voice_id': self.voice_id,
            'model_id': self.model_id,
            'language': self.audio_language.name
        }

    def get_voice_shortname(self):
        return f'{self.name} ({self.model_short_name})'

    def get_options(self):
        return VOICE_OPTIONS

class ElevenLabsService(cloudlanguagetools.service.Service):
    def __init__(self):
        self.service = cloudlanguagetools.constants.Service.ElevenLabs

    def configure(self, config):
        self.api_key = config['api_key']

    def get_headers(self):
        return {
            "Accept": "application/json",
            "xi-api-key": self.api_key
        }

    def get_tts_audio(self, text, voice_key, options):
        voice_id = voice_key['voice_id']
        url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'

        response_format_parameter, audio_format = self.get_request_audio_format({
            AudioFormat.mp3: 'mp3_44100_128',
            AudioFormat.wav: 'pcm_44100'
        }, options, AudioFormat.mp3)

        headers = self.get_headers()
        headers['Accept'] = "audio/mpeg"

        data = {
            "text": text,
            "model_id": voice_key['model_id'],
            "voice_settings": {
                "stability": options.get('stability', DEFAULT_STABILITY),
                "similarity_boost": options.get('similarity_boost', DEFAULT_SIMILARITY_BOOST)
            }
        }

        query_params = {
            'output_format': response_format_parameter
        }
        full_url = f'{url}?{urllib.parse.urlencode(query_params)}'

        if audio_format == cloudlanguagetools.options.AudioFormat.wav:
            return cloudlanguagetools.audio_processing.wrap_pcm_data_wave(self.get_tts_audio_base_post_request(full_url, json=data, headers=headers), 
                num_channels=1,
                sample_width=2, 
                framerate=44100) # pcm_44100 - PCM format (S16LE) with 44.1kHz sample rate. 
        return self.get_tts_audio_base_post_request(full_url, json=data, headers=headers)



    def get_audio_language(self, language_id) -> cloudlanguagetools.languages.AudioLanguage:
        logger.debug(f'processing language_id: {language_id}')
        override_map = {
            'pt': cloudlanguagetools.languages.AudioLanguage.pt_PT,
            'en-uk': cloudlanguagetools.languages.AudioLanguage.en_GB,
            'zh': cloudlanguagetools.languages.AudioLanguage.zh_CN,
            'id': cloudlanguagetools.languages.AudioLanguage.id_ID
        }
        if language_id in override_map:
            return override_map[language_id]
        # try to reconstruct AudioLanguage
        language_id_components = language_id.split('-')
        if len(language_id_components) != 2:
            language_enum = cloudlanguagetools.languages.Language[language_id]
            audio_language_enum = cloudlanguagetools.languages.AudioLanguageDefaults[language_enum]
            return audio_language_enum
        else:
            # language is in format en-us
            modified_language_id = language_id_components[0] + '_' + language_id_components[1].upper()
            logger.debug(f'modified_language_id: {modified_language_id}')
            audio_language_enum = cloudlanguagetools.languages.AudioLanguage[modified_language_id]
            return audio_language_enum

    def get_tts_voice_list(self) -> List[ElevenLabsVoice]:
        result = []

        # first, get all models to get list of languages
        url = "https://api.elevenlabs.io/v1/models"
        response = requests.get(url, headers=self.get_headers(), timeout=cloudlanguagetools.constants.RequestTimeout)
        response.raise_for_status()
        model_data = response.json()

        # restrict to models that can do text to speech (elevenlabs introduced voice conversion)
        model_data = [model for model in model_data if model['can_do_text_to_speech']]

        #pprint.pprint(model_data)
        # model_data: 
        # [{'can_be_finetuned': True,
        # 'can_do_text_to_speech': True,
        # 'can_do_voice_conversion': False,
        # 'description': 'Use our standard English language model to generate speech '
        #                 'in a variety of voices, styles and moods.',
        # 'languages': [{'language_id': 'en', 'name': 'English'}],
        # 'model_id': 'eleven_monolingual_v1',
        # 'name': 'Eleven Monolingual v1',
        # 'token_cost_factor': 1.0},
        # {'can_be_finetuned': True,
        # 'can_do_text_to_speech': True,
        # 'can_do_voice_conversion': True,
        # 'description': 'Generate lifelike speech in multiple languages and create '
        #                 'content that resonates with a broader audience. ',
        # 'languages': [{'language_id': 'en', 'name': 'English'},
        #                 {'language_id': 'de', 'name': 'German'},
        #                 {'language_id': 'pl', 'name': 'Polish'},
        #                 {'language_id': 'es', 'name': 'Spanish'},
        #                 {'language_id': 'it', 'name': 'Italian'},
        #                 {'language_id': 'fr', 'name': 'French'},
        #                 {'language_id': 'pt', 'name': 'Portuguese'},
        #                 {'language_id': 'hi', 'name': 'Hindi'}],
        # 'model_id': 'eleven_multilingual_v1',
        # 'name': 'Eleven Multilingual v1',
        # 'token_cost_factor': 1.0}]
        #         


        # now, retrieve voice list
        # call elevenlabs API to list TTS voices
        url = "https://api.elevenlabs.io/v1/voices"

        response = requests.get(url, headers=self.get_headers(), timeout=cloudlanguagetools.constants.RequestTimeout)
        response.raise_for_status()

        data = response.json()

        for model in model_data:
            model_id = model['model_id']
            model_name = model['name']
            model_short_name = model_name.replace('Eleven ', '').strip()
            for language_record in model['languages']:
                try:
                    language_id = language_record['language_id']
                    audio_language_enum = self.get_audio_language(language_id)
                    for voice_data in data['voices']:
                        result.append(ElevenLabsVoice(voice_data, audio_language_enum, model_id, model_short_name))
                except Exception as e:
                    logger.exception(f'ElevenLabs: error processing voice_data: {voice_data}')

        return result


    def get_tts_voice_list_v3(self) -> List[cloudlanguagetools.ttsvoice.TtsVoice_v3]:
        result = []

        # first, get all models to get list of languages
        url = "https://api.elevenlabs.io/v1/models"
        response = requests.get(url, headers=self.get_headers(), timeout=cloudlanguagetools.constants.RequestTimeout)
        response.raise_for_status()
        model_data = response.json()

        # restrict to models that can do text to speech (elevenlabs introduced voice conversion)
        model_data = [model for model in model_data if model['can_do_text_to_speech']]

        #pprint.pprint(model_data)
        # model_data: 
        # [{'can_be_finetuned': True,
        # 'can_do_text_to_speech': True,
        # 'can_do_voice_conversion': False,
        # 'description': 'Use our standard English language model to generate speech '
        #                 'in a variety of voices, styles and moods.',
        # 'languages': [{'language_id': 'en', 'name': 'English'}],
        # 'model_id': 'eleven_monolingual_v1',
        # 'name': 'Eleven Monolingual v1',
        # 'token_cost_factor': 1.0},
        # {'can_be_finetuned': True,
        # 'can_do_text_to_speech': True,
        # 'can_do_voice_conversion': True,
        # 'description': 'Generate lifelike speech in multiple languages and create '
        #                 'content that resonates with a broader audience. ',
        # 'languages': [{'language_id': 'en', 'name': 'English'},
        #                 {'language_id': 'de', 'name': 'German'},
        #                 {'language_id': 'pl', 'name': 'Polish'},
        #                 {'language_id': 'es', 'name': 'Spanish'},
        #                 {'language_id': 'it', 'name': 'Italian'},
        #                 {'language_id': 'fr', 'name': 'French'},
        #                 {'language_id': 'pt', 'name': 'Portuguese'},
        #                 {'language_id': 'hi', 'name': 'Hindi'}],
        # 'model_id': 'eleven_multilingual_v1',
        # 'name': 'Eleven Multilingual v1',
        # 'token_cost_factor': 1.0}]
        #         


        # now, retrieve voice list
        # call elevenlabs API to list TTS voices
        url = "https://api.elevenlabs.io/v1/voices"

        response = requests.get(url, headers=self.get_headers(), timeout=cloudlanguagetools.constants.RequestTimeout)
        response.raise_for_status()

        data = response.json()

        for model in model_data:
            model_id = model['model_id']
            model_name = model['name']
            model_short_name = model_name.replace('Eleven ', '').strip()
            # for language_record in model['languages']:
            for voice_data in data['voices']:
                voice_name = voice_data['name']
                try:
                    languages = model['languages']
                    language_id_list = [language_record['language_id'] for language_record in languages]
                    audio_language_enum_list = [self.get_audio_language(language_id) for language_id in language_id_list]
                    voice = cloudlanguagetools.ttsvoice.TtsVoice_v3(
                        name=f'{voice_name} ({model_short_name})',
                        voice_key={
                            'voice_id': voice_data['voice_id'],
                            'model_id': model_id,
                        },
                        options=VOICE_OPTIONS,
                        service=cloudlanguagetools.constants.Service.ElevenLabs,
                        gender=GENDER_MAP.get(voice_data['labels']['gender'], cloudlanguagetools.constants.Gender.Male),
                        audio_languages=audio_language_enum_list,
                        service_fee=cloudlanguagetools.constants.ServiceFee.paid
                    )
                    result.append(voice)
                except Exception as e:
                    logger.exception(f'ElevenLabs: error processing voice_data: {voice_data}')

        return result

