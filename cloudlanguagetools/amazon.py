import json
import requests
import tempfile
import boto3
import botocore.exceptions
import contextlib

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
        # print(voice_data)
        # {'Gender': 'Female', 'Id': 'Lotte', 'LanguageCode': 'nl-NL', 'LanguageName': 'Dutch', 'Name': 'Lotte', 'SupportedEngines': ['standard']}
        self.service = cloudlanguagetools.constants.Service.Amazon
        self.gender = cloudlanguagetools.constants.Gender[voice_data['Gender']]
        self.voice_id = voice_data['Id']
        self.name = voice_data['Name']
        self.audio_language = get_audio_language_enum(voice_data['LanguageCode'])
        self.engine = 'standard'
        if 'neural' in voice_data['SupportedEngines']:
            self.engine = 'neural'

    def get_voice_key(self):
        return {
            'voice_id': self.voice_id,
            'engine': self.engine
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

        try:
            response = self.polly_client.synthesize_speech(Text=text, OutputFormat="mp3", VoiceId=voice_key['voice_id'], Engine=voice_key['engine'])
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as error:
            raise cloudlanguagetools.errors.RequestError(str(error))

        if "AudioStream" in response:
            # Note: Closing the stream is important because the service throttles on the
            # number of parallel connections. Here we are using contextlib.closing to
            # ensure the close method of the stream object will be called automatically
            # at the end of the with statement's scope.
            with contextlib.closing(response["AudioStream"]) as stream:
                with open(output_temp_filename, 'wb') as audio:
                    audio.write(stream.read())
                return output_temp_file

        else:
            # The response didn't contain audio data, exit gracefully
            raise cloudlanguagetools.errors.RequestError('no audio stream')


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
   