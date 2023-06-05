import json
import requests
import tempfile
import os
import boto3
import botocore.exceptions
import contextlib

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.options
import cloudlanguagetools.languages
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.translationlanguage
import cloudlanguagetools.transliterationlanguage
import cloudlanguagetools.errors

DEFAULT_VOICE_PITCH = 0
DEFAULT_VOICE_RATE = 100

def get_audio_language_enum(language_code):
    language_map = {
        'arb': 'ar_XA',
        'cmn-CN': 'zh_CN',
        'yue-CN': 'zh_HK'
    }

    language_enum_name = language_code.replace('-', '_')
    if language_code in language_map:
        language_enum_name = language_map[language_code]

    return cloudlanguagetools.languages.AudioLanguage[language_enum_name]

class AmazonVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, voice_data):
        # print(voice_data)
        # {'Gender': 'Female', 'Id': 'Lotte', 'LanguageCode': 'nl-NL', 'LanguageName': 'Dutch', 'Name': 'Lotte', 'SupportedEngines': ['standard']}
        self.service = cloudlanguagetools.constants.Service.Amazon
        self.service_fee = cloudlanguagetools.constants.ServiceFee.paid
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
        return f'{self.name} ({self.engine.capitalize()})'

    def get_options(self):
        return {
            'rate' : {
                'type': 'number',
                'min': 20,
                'max': 200,
                'default': DEFAULT_VOICE_RATE
            },
            'pitch': {
                'type': 'number',
                'min': -50,
                'max': 50,
                'default': DEFAULT_VOICE_PITCH
            },
            cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER: {
                'type': cloudlanguagetools.options.ParameterType.list.name,
                'values': [
                    cloudlanguagetools.options.AudioFormat.mp3.name,
                    cloudlanguagetools.options.AudioFormat.ogg_vorbis.name,
                ],
                'default': cloudlanguagetools.options.AudioFormat.mp3.name
            }            
        }

class AmazonTranslationLanguage(cloudlanguagetools.translationlanguage.TranslationLanguage):
    def __init__(self, language, language_id):
        self.service = cloudlanguagetools.constants.Service.Amazon
        self.service_fee = cloudlanguagetools.constants.ServiceFee.paid
        self.language = language
        self.language_id = language_id

    def get_language_id(self):
        return self.language_id

class ElevenLabsService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def configure(self, config):
        self.api_key = config['api_key']

    def get_translation(self, text, from_language_key, to_language_key):
        result = self.translate_client.translate_text(Text=text, 
                    SourceLanguageCode=from_language_key, TargetLanguageCode=to_language_key)
        return result.get('TranslatedText')

    def get_tts_audio(self, text, voice_key, options):
        audio_format_str = options.get(cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER, cloudlanguagetools.options.AudioFormat.mp3.name)
        audio_format = cloudlanguagetools.options.AudioFormat[audio_format_str]

        audio_format_map = {
            cloudlanguagetools.options.AudioFormat.mp3: 'mp3',
            cloudlanguagetools.options.AudioFormat.ogg_vorbis: 'ogg_vorbis'
        }

        output_temp_file = tempfile.NamedTemporaryFile()
        output_temp_filename = output_temp_file.name

        pitch = options.get('pitch', DEFAULT_VOICE_PITCH)
        pitch_str = f'{pitch:+.0f}%'
        rate = options.get('rate', DEFAULT_VOICE_RATE)
        rate_str = f'{rate:0.0f}%'

        prosody_tags = f'pitch="{pitch_str}" rate="{rate_str}"'
        if voice_key['engine'] == 'neural':
            # pitch not supported on neural voices
            prosody_tags = f'rate="{rate_str}"'


        ssml_str = f"""<speak>
    <prosody {prosody_tags} >
        {text}
    </prosody>
</speak>"""

        try:
            response = self.polly_client.synthesize_speech(Text=ssml_str, TextType="ssml", OutputFormat=audio_format_map[audio_format], VoiceId=voice_key['voice_id'], Engine=voice_key['engine'])
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
        # call elevenlabs API to list TTS voices
        url = "https://api.elevenlabs.io/v1/voices"

        headers = {
            "Accept": "application/json",
            "xi-api-key": self.api_key
        }

        response = requests.get(url, headers=headers)

        print(response.text)

        return result

