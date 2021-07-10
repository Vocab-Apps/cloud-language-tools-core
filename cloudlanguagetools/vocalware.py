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

class VocalWareVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, audio_language, name, gender, language_id, voice_id, engine_id):
        self.service = cloudlanguagetools.constants.Service.VocalWare
        self.audio_language = audio_language
        self.name = name
        self.gender = gender
        self.language_id = language_id
        self.voice_id = voice_id
        self.engine_id = engine_id

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


class VocalWareService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def configure(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    def get_translation(self, text, from_language_key, to_language_key):
        url = 'https://naveropenapi.apigw.ntruss.com/nmt/v1/translation'
        headers = {
            'X-NCP-APIGW-API-KEY-ID': self.client_id,
            'X-NCP-APIGW-API-KEY': self.client_secret
        }

        data = {
            'text': text,
            'source': from_language_key,
            'target': to_language_key
        }

        # alternate_data = 'speaker=clara&text=vehicle&volume=0&speed=0&pitch=0&format=mp3'
        response = requests.post(url, json=data, headers=headers, timeout=cloudlanguagetools.constants.RequestTimeout)
        if response.status_code == 200:
            response_data = response.json()
            return response_data['message']['result']['translatedText']

        error_message = f'Status code: {response.status_code}: {response.content}'
        raise cloudlanguagetools.errors.RequestError(error_message)


    def get_tts_audio(self, text, voice_key, options):
        output_temp_file = tempfile.NamedTemporaryFile()
        output_temp_filename = output_temp_file.name

        url = 'https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-NCP-APIGW-API-KEY-ID': self.client_id,
            'X-NCP-APIGW-API-KEY': self.client_secret
        }

        data = {
            'text': text,
            'speaker': voice_key['name'],
            'speed': options.get('speed', NAVER_VOICE_SPEED_DEFAULT),
            'pitch': options.get('pitch', NAVER_VOICE_PITCH_DEFAULT)
        }

        # alternate_data = 'speaker=clara&text=vehicle&volume=0&speed=0&pitch=0&format=mp3'
        response = requests.post(url, data=data, headers=headers, timeout=cloudlanguagetools.constants.RequestTimeout)
        if response.status_code == 200:
            with open(output_temp_filename, 'wb') as audio:
                audio.write(response.content)
            return output_temp_file

        response_data = json.loads(response.content)['error']
        error_message = f'Status code: {response.status_code}: {response_data}'
        raise cloudlanguagetools.errors.RequestError(error_message)

    def get_tts_voice_list(self):
        # returns list of TtSVoice
        return [
            VocalWareVoice(cloudlanguagetools.constants.AudioLanguage.en_US, 'Dave (US)', cloudlanguagetools.constants.Gender.Male, 1, 2, 2),            
        ]

    def get_translation_language_list(self):
        result = []
        return result

    def get_transliteration_language_list(self):
        result = []
        return result
   