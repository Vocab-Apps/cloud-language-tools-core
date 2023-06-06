import json
import pprint
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


GENDER_MAP = {
    'Rachel': cloudlanguagetools.constants.Gender.Female
}


class ElevenLabsVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, voice_data, language, model_id):
        # pprint.pprint(voice_data)
        self.service = cloudlanguagetools.constants.Service.ElevenLabs
        self.service_fee = cloudlanguagetools.constants.ServiceFee.paid
        self.voice_id = voice_data['voice_id']
        self.model_id = model_id
        self.name = voice_data['name']
        self.gender = GENDER_MAP.get(self.name, cloudlanguagetools.constants.Gender.Male)
        self.audio_language = language

    def get_voice_key(self):
        return {
            'voice_id': self.voice_id,
            'model_id': self.model_id
        }

    def get_voice_shortname(self):
        return f'{self.name}'

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

    def get_headers(self):
        return {
            "Accept": "application/json",
            "xi-api-key": self.api_key
        }

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


    def get_audio_language(self, language_id):
        override_map = {
            'pt': cloudlanguagetools.languages.AudioLanguage.pt_PT,
        }
        if language_id in override_map:
            return override_map[language_id]
        language_enum = cloudlanguagetools.languages.Language[language_id]
        audio_language_enum = cloudlanguagetools.languages.language_map_to_audio_language[language_enum]
        return audio_language_enum

    def get_tts_voice_list(self):
        result = []

        # first, get all models to get list of languages
        url = "https://api.elevenlabs.io/v1/models"
        response = requests.get(url, headers=self.get_headers())
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
        # keep only the model which has multiple language entries
        multilingual_model_data = [model for model in model_data if len(model['languages']) > 1][0]
        model_id = multilingual_model_data['model_id']


        # now, retrieve voice list
        # call elevenlabs API to list TTS voices
        url = "https://api.elevenlabs.io/v1/voices"

        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()

        data = response.json()

        for language_record in multilingual_model_data['languages']:
            language_id = language_record['language_id']
            audio_language_enum = self.get_audio_language(language_id)
            for voice_data in data['voices']:
                result.append(ElevenLabsVoice(voice_data, audio_language_enum, model_id))

        return result

