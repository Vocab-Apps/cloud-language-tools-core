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
        pass

    def configure(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

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
        response = requests.post(url, data=data, headers=headers)
        if response.status_code == 200:
            with open(output_temp_filename, 'wb') as audio:
                audio.write(response.content)
            return output_temp_file

        error_message = f'Status code: {response.status_code}: {response.content}'
        raise cloudlanguagetools.errors.RequestError(error_message)

    def get_tts_voice_list(self):
        # returns list of TtSVoice
        return [
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ko_KR, 'mijin', cloudlanguagetools.constants.Gender.Female, 'Mijin', 'General'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ko_KR, 'jinho', cloudlanguagetools.constants.Gender.Male, 'Jinho', 'General'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.en_US, 'clara', cloudlanguagetools.constants.Gender.Female, 'Clara', 'General'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.en_US, 'matt', cloudlanguagetools.constants.Gender.Male, 'Matt', 'General'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ja_JP, 'shinji', cloudlanguagetools.constants.Gender.Male, 'Shinji', 'General'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.zh_CN, 'meimei', cloudlanguagetools.constants.Gender.Female, 'Meimei', 'General'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.zh_CN, 'liangliang', cloudlanguagetools.constants.Gender.Male, 'Liangliang', 'General'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.es_ES, 'jose', cloudlanguagetools.constants.Gender.Male, 'Jose', 'General'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.es_ES, 'carmen', cloudlanguagetools.constants.Gender.Female, 'Carmen', 'General'),

            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ko_KR, 'nara', cloudlanguagetools.constants.Gender.Female, 'Nara', 'Premium'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ko_KR, 'nminsang', cloudlanguagetools.constants.Gender.Male, 'Minsang', 'Premium'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ko_KR, 'nhajun', cloudlanguagetools.constants.Gender.Male, 'Hajoon', 'Premium (Child)'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ko_KR, 'ndain', cloudlanguagetools.constants.Gender.Female, 'Dain', 'Premium (Child)'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ko_KR, 'njiyun', cloudlanguagetools.constants.Gender.Female, 'Jiyoon', 'Premium'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ko_KR, 'nsujin', cloudlanguagetools.constants.Gender.Female, 'Sujin', 'Premium'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ko_KR, 'njinho', cloudlanguagetools.constants.Gender.Male, 'Jinho', 'Premium'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ko_KR, 'nsinu', cloudlanguagetools.constants.Gender.Male, 'Shinwoo', 'Premium'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ko_KR, 'njihun', cloudlanguagetools.constants.Gender.Male, 'Jihoon', 'Premium'),

            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ja_JP, 'ntomoko', cloudlanguagetools.constants.Gender.Female, 'Tomoko', 'Premium'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ja_JP, 'nnaomi', cloudlanguagetools.constants.Gender.Female, 'Naomi', 'Premium'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ja_JP, 'nsayuri', cloudlanguagetools.constants.Gender.Female, 'Sayuri', 'Premium'),

            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ko_KR, 'ngoeun', cloudlanguagetools.constants.Gender.Female, 'Koeun', 'Premium'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ko_KR, 'neunyoung', cloudlanguagetools.constants.Gender.Female, 'Eunyoung', 'Premium'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ko_KR, 'nsunkyung', cloudlanguagetools.constants.Gender.Female, 'Sunkyung', 'Premium'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ko_KR, 'nyujin', cloudlanguagetools.constants.Gender.Female, 'Yujin', 'Premium'),
            
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ko_KR, 'ntaejin', cloudlanguagetools.constants.Gender.Male, 'Taejin', 'Premium'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ko_KR, 'nyoungil', cloudlanguagetools.constants.Gender.Male, 'Youngil', 'Premium'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ko_KR, 'nseungpyo', cloudlanguagetools.constants.Gender.Male, 'Seungpyo', 'Premium'),
            NaverVoice(cloudlanguagetools.constants.AudioLanguage.ko_KR, 'nwontak', cloudlanguagetools.constants.Gender.Male, 'Wontak', 'Premium'),
        ]

    def get_translation_language_list(self):
        result = []
        return result

    def get_transliteration_language_list(self):
        result = []
        return result
   