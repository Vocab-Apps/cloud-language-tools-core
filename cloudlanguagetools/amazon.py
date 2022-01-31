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
        self.polly_client = boto3.client("polly", 
            config=botocore.config.Config(connect_timeout=cloudlanguagetools.constants.RequestTimeout, read_timeout=cloudlanguagetools.constants.RequestTimeout))
        self.translate_client = boto3.client("translate",
            config=botocore.config.Config(connect_timeout=cloudlanguagetools.constants.RequestTimeout, read_timeout=cloudlanguagetools.constants.RequestTimeout))

    def get_translation(self, text, from_language_key, to_language_key):
        result = self.translate_client.translate_text(Text=text, 
                    SourceLanguageCode=from_language_key, TargetLanguageCode=to_language_key)
        return result.get('TranslatedText')

    def get_tts_audio(self, text, voice_key, options):
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
            response = self.polly_client.synthesize_speech(Text=ssml_str, TextType="ssml", OutputFormat="mp3", VoiceId=voice_key['voice_id'], Engine=voice_key['engine'])
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
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.af, 'af'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.sq, 'sq'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.am, 'am'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.ar, 'ar'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.hy, 'hy'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.az, 'az'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.bn, 'bn'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.bs, 'bs'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.bg, 'bg'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.ca, 'ca'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.zh_cn, 'zh'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.zh_tw, 'zh-TW'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.hr, 'hr'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.cs, 'cs'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.da, 'da'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.prs, 'fa-AF'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.nl, 'nl'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.en, 'en'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.et, 'et'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.fa, 'fa'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.tl, 'tl'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.fi, 'fi'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.fr, 'fr'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.fr_ca, 'fr-CA'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.ka, 'ka'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.de, 'de'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.el, 'el'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.gu, 'gu'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.ht, 'ht'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.ha, 'ha'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.he, 'he'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.hi, 'hi'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.hu, 'hu'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.is_, 'is'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.id_, 'id'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.it, 'it'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.ja, 'ja'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.kn, 'kn'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.kk, 'kk'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.ko, 'ko'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.lv, 'lv'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.lt, 'lt'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.mk, 'mk'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.ms, 'ms'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.ml, 'ml'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.mt, 'mt'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.mn, 'mn'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.no, 'no'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.fa, 'fa'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.ps, 'ps'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.pl, 'pl'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.pt_pt, 'pt'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.ro, 'ro'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.ru, 'ru'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.sr_cyrl, 'sr'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.si, 'si'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.sk, 'sk'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.sl, 'sl'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.so, 'so'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.es, 'es'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.es_mx, 'es-MX'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.sw, 'sw'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.sv, 'sv'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.tl, 'tl'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.ta, 'ta'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.te, 'te'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.th, 'th'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.tr, 'tr'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.uk, 'uk'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.ur, 'ur'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.uz, 'uz'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.vi, 'vi'),
            AmazonTranslationLanguage(cloudlanguagetools.constants.Language.cy, 'cy')
        ]
        return result

    def get_transliteration_language_list(self):
        result = []
        return result
   