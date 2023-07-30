import json
import pprint
import requests
import tempfile
import os
import contextlib
from typing import List

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.options
import cloudlanguagetools.languages
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.translationlanguage
import cloudlanguagetools.transliterationlanguage
import cloudlanguagetools.errors


DEFAULT_STABILITY = 0.75
DEFAULT_SIMILARITY_BOOST = 0.75

GENDER_MAP = {
    'male': cloudlanguagetools.constants.Gender.Male,
    'female': cloudlanguagetools.constants.Gender.Female,
}

class ElevenLabsVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, voice_data, language, model_id, model_short_name):
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
            'model_id': self.model_id
        }

    def get_voice_shortname(self):
        return f'{self.name} ({self.model_short_name})'

    def get_options(self):
        return {
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
        }

class ElevenLabsService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def configure(self, config):
        self.api_key = config['api_key']

    def get_headers(self):
        return {
            "Accept": "application/json",
            "xi-api-key": self.api_key
        }

    def get_tts_audio(self, text, voice_key, options):
        import requests

        CHUNK_SIZE = 1024
        voice_id = voice_key['voice_id']
        url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'

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

        response = requests.post(url, json=data, headers=headers, timeout=cloudlanguagetools.constants.RequestTimeout)
        response.raise_for_status()
        
        output_temp_file = tempfile.NamedTemporaryFile()
        output_temp_filename = output_temp_file.name

        with open(output_temp_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)

        return output_temp_file


    def get_audio_language(self, language_id):
        override_map = {
            'pt': cloudlanguagetools.languages.AudioLanguage.pt_PT,
        }
        if language_id in override_map:
            return override_map[language_id]
        language_enum = cloudlanguagetools.languages.Language[language_id]
        audio_language_enum = cloudlanguagetools.languages.AudioLanguageDefaults[language_enum]
        return audio_language_enum

    def get_tts_voice_list(self) -> List[ElevenLabsVoice]:
        result = []

        # first, get all models to get list of languages
        url = "https://api.elevenlabs.io/v1/models"
        response = requests.get(url, headers=self.get_headers(), timeout=cloudlanguagetools.constants.RequestTimeout)
        response.raise_for_status()
        model_data = response.json()
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
            model_short_name = model_name.replace('Eleven ', '').replace('v1', '').strip()
            for language_record in model['languages']:
                language_id = language_record['language_id']
                audio_language_enum = self.get_audio_language(language_id)
                for voice_data in data['voices']:
                    result.append(ElevenLabsVoice(voice_data, audio_language_enum, model_id, model_short_name))

        return result

