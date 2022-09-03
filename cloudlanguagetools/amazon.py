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
        'cmn-CN': 'zh_CN'
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
        self.language = language
        self.language_id = language_id

    def get_language_id(self):
        return self.language_id

class AmazonService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def configure(self, config):
        aws_access_key_id = config['AWS_ACCESS_KEY_ID']
        aws_secret_access_key = config['AWS_SECRET_ACCESS_KEY']
        region_name = config['AWS_DEFAULT_REGION']

        self.polly_client = boto3.client("polly", 
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            config=botocore.config.Config(connect_timeout=cloudlanguagetools.constants.RequestTimeout, read_timeout=cloudlanguagetools.constants.RequestTimeout))
        self.translate_client = boto3.client("translate",
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,        
            config=botocore.config.Config(connect_timeout=cloudlanguagetools.constants.RequestTimeout, read_timeout=cloudlanguagetools.constants.RequestTimeout))

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
        response = self.polly_client.describe_voices()
        # print(response['Voices'])
        for voice in response['Voices']:
            result.append(AmazonVoice(voice))
        return result


    def get_translation_language_list(self):
        result = [
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.af, 'af'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.sq, 'sq'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.am, 'am'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.ar, 'ar'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.hy, 'hy'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.az, 'az'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.bn, 'bn'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.bs, 'bs'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.bg, 'bg'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.ca, 'ca'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.zh_cn, 'zh'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.zh_tw, 'zh-TW'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.hr, 'hr'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.cs, 'cs'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.da, 'da'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.prs, 'fa-AF'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.nl, 'nl'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.en, 'en'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.et, 'et'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.fa, 'fa'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.tl, 'tl'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.fi, 'fi'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.fr, 'fr'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.fr_ca, 'fr-CA'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.ka, 'ka'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.de, 'de'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.el, 'el'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.gu, 'gu'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.ht, 'ht'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.ha, 'ha'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.he, 'he'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.hi, 'hi'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.hu, 'hu'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.is_, 'is'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.id_, 'id'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.it, 'it'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.ja, 'ja'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.kn, 'kn'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.kk, 'kk'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.ko, 'ko'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.lv, 'lv'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.lt, 'lt'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.mk, 'mk'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.ms, 'ms'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.ml, 'ml'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.mt, 'mt'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.mn, 'mn'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.no, 'no'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.fa, 'fa'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.ps, 'ps'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.pl, 'pl'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.pt_pt, 'pt'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.ro, 'ro'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.ru, 'ru'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.sr_cyrl, 'sr'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.si, 'si'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.sk, 'sk'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.sl, 'sl'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.so, 'so'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.es, 'es'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.es_mx, 'es-MX'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.sw, 'sw'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.sv, 'sv'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.tl, 'tl'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.ta, 'ta'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.te, 'te'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.th, 'th'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.tr, 'tr'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.uk, 'uk'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.ur, 'ur'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.uz, 'uz'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.vi, 'vi'),
            AmazonTranslationLanguage(cloudlanguagetools.languages.Language.cy, 'cy')
        ]
        return result

    def get_transliteration_language_list(self):
        result = []
        return result
   