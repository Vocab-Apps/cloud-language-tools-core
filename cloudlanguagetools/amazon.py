import json
import requests
import boto3

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.translationlanguage
import cloudlanguagetools.transliterationlanguage
import cloudlanguagetools.errors


def get_audio_language_enum(language_code):
    language_map = {
        'arb': 'ar_XA',
        'cmn-CN': 'zh_CN'
    }

    language_enum_name = language_code.replace('-', '_')
    if language_code in language_map:
        language_enum_name = language_map[language_code]

    return cloudlanguagetools.constants.AudioLanguage[language_enum_name]

class AmazonVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, voice_data):
        print(voice_data)
        # {'Gender': 'Female', 'Id': 'Lotte', 'LanguageCode': 'nl-NL', 'LanguageName': 'Dutch', 'Name': 'Lotte', 'SupportedEngines': ['standard']}
        self.service = cloudlanguagetools.constants.Service.Amazon
        self.gender = cloudlanguagetools.constants.Gender[voice_data['Gender']]
        self.name = voice_data['Id']
        self.audio_language = get_audio_language_enum(voice_data['LanguageCode'])

    def get_voice_key(self):
        return {
            'name': self.name
        }

    def get_voice_shortname(self):
        return f'{self.name}'

    def get_options(self):
        return {
        }

class AmazonTranslationLanguage(cloudlanguagetools.translationlanguage.TranslationLanguage):
    def __init__(self, language, language_id):
        self.service = cloudlanguagetools.constants.Service.Amazon
        self.language = language
        self.language_id = language_id

    def get_language_id(self):
        return self.language_id

class AmazonService(cloudlanguagetools.service.Service):
    def __init__(self):
        self.polly_client = boto3.client("polly")

    def get_translation(self, text, from_language_key, to_language_key):
        url = 'https://Amazonopenapi.apigw.ntruss.com/nmt/v1/translation'
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
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            response_data = response.json()
            return response_data['message']['result']['translatedText']

        error_message = f'Status code: {response.status_code}: {response.content}'
        raise cloudlanguagetools.errors.RequestError(error_message)


    def get_tts_audio(self, text, voice_key, options):
        output_temp_file = tempfile.NamedTemporaryFile()
        output_temp_filename = output_temp_file.name

        url = 'https://Amazonopenapi.apigw.ntruss.com/tts-premium/v1/tts'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-NCP-APIGW-API-KEY-ID': self.client_id,
            'X-NCP-APIGW-API-KEY': self.client_secret
        }

        data = {
            'text': text,
            'speaker': voice_key['name'],
            'speed': options.get('speed', Amazon_VOICE_SPEED_DEFAULT),
            'pitch': options.get('pitch', Amazon_VOICE_PITCH_DEFAULT)
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
        result = []
        response = self.polly_client.describe_voices()
        # print(response['Voices'])
        for voice in response['Voices']:
            result.append(AmazonVoice(voice))
        return result


    def get_translation_language_list(self):
        result = [
        ]
        return result

    def get_transliteration_language_list(self):
        result = []
        return result
   