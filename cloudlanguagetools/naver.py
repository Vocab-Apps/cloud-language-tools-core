import json
import requests
import tempfile
import uuid
import operator
import pydub

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.translationlanguage
import cloudlanguagetools.transliterationlanguage
import cloudlanguagetools.errors

NAVER_VOICE_SPEED_DEFAULT = 0
NAVER_VOICE_PITCH_DEFAULT = 0

class NaverVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, audio_language, name, gender, description, voice_type):
        self.service = cloudlanguagetools.constants.Service.Naver
        self.audio_language = audio_language
        self.name = name
        self.gender = gender
        self.description = description
        self.voice_type = voice_type

    def get_voice_key(self):
        return {
            'name': self.name
        }

    def get_voice_shortname(self):
        return f'{self.description} ({self.voice_type})'

    def get_options(self):
        return {
            'speed' : {
                'type': 'number_int',
                'min': -5,
                'max': 5,
                'default': NAVER_VOICE_SPEED_DEFAULT
            },
            'pitch': {
                'type': 'number_int',
                'min': -5,
                'max': 5,
                'default': NAVER_VOICE_PITCH_DEFAULT
            }
        }

class NaverService(cloudlanguagetools.service.Service):
    def __init__(self):
        self.url_translator_base = 'https://api.cognitive.microsofttranslator.com'

    def configure(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    def get_tts_audio(self, text, voice_key, options):
        output_temp_file = tempfile.NamedTemporaryFile()
        output_temp_filename = output_temp_file.name

        url = 'https://naveropenapi.apigw.ntruss.com/voice-premium/v1/tts'
        headers = {
            'X-NCP-APIGW-API-KEY-ID': self.client_id,
            'X-NCP-APIGW-API-KEY': self.client_secret
        }

        data = {
            'text': text,
            'speaker': voice_key['name'],
            'speed': options['speed'],
            'pitch': options['pitch']
        }

        response = requests.post(url, data, headers=headers)
        if response.status_code == 200:
            with open(output_temp_filename, 'wb') as audio:
                audio.write(response.content)
            return output_temp_file

        error_message = f'Status code: {response.status_code}: {response}'
        raise cloudlanguagetools.errors.RequestError(error_message)

    def get_tts_voice_list(self):
        # returns list of TtSVoice
        return [
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ko_KR, 'nara', cloudlanguagetools.constants.Gender.Female, 'Nara', 'Premium')
        ]

    def get_translation_language_list(self):
        result = []
        return result

    def get_transliteration_language_list(self):
        result = []
        return result
   