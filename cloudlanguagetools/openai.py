from openai import OpenAI

import copy
import logging
import tempfile
import pydub
import pprint
from typing import List

import cloudlanguagetools.constants
import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.options

from cloudlanguagetools.languages import AudioLanguage
from cloudlanguagetools.options import AudioFormat

logger = logging.getLogger(__name__)

DEFAULT_TTS_SPEED = 1.0
DEFAULT_INSTRUCTIONS = ''
DEFAULT_MODEL = 'tts-1-hd'
DEFAULT_MODEL_GPT_4O = 'gpt-4o-mini-tts'

MODELS_ALL = [
    'gpt-4o-mini-tts',
    'tts-1-hd',
    'tts-1'
]

MODELS_GPT_4O_ONLY = [
    'gpt-4o-mini-tts'
]

VOICE_OPTIONS = {
            'speed' : {
                'type': cloudlanguagetools.options.ParameterType.number.name,
                'min': 0.25,
                'max': 4.0,
                'default': DEFAULT_TTS_SPEED
            },
            'instructions':
            {
                'type': cloudlanguagetools.options.ParameterType.text.name,
                'default': DEFAULT_INSTRUCTIONS
            },
            'model':
            {
                'type': cloudlanguagetools.options.ParameterType.list.name,
                'values': [
                    'gpt-4o-mini-tts',
                    'tts-1-hd',
                    'tts-1'
                ],
                'default': DEFAULT_MODEL
            },
            cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER: {
                'type': cloudlanguagetools.options.ParameterType.list.name,
                'values': [
                    cloudlanguagetools.options.AudioFormat.mp3.name,
                    cloudlanguagetools.options.AudioFormat.ogg_opus.name,
                    cloudlanguagetools.options.AudioFormat.wav.name
                ],
                'default': cloudlanguagetools.options.AudioFormat.mp3.name
            }
}

# https://platform.openai.com/docs/guides/text-to-speech#voice-options
# Afrikaans, Arabic, Armenian, Azerbaijani, Belarusian, Bosnian, Bulgarian, Catalan, 
# Chinese, Croatian, Czech, Danish, Dutch, English, Estonian, Finnish, French, Galician, 
# German, Greek, Hebrew, Hindi, Hungarian, Icelandic, Indonesian, Italian, Japanese, 
# Kannada, Kazakh, Korean, Latvian, Lithuanian, Macedonian, Malay, Marathi, Maori, 
# Nepali, Norwegian, Persian, Polish, Portuguese, Romanian, Russian, Serbian, Slovak, 
# Slovenian, Spanish, Swahili, Swedish, Tagalog, Tamil, Thai, Turkish, Ukrainian, 
# Urdu, Vietnamese, and Welsh.

TTS_SUPPORTED_LANGUAGES = [
            AudioLanguage.af_ZA,
            AudioLanguage.ar_XA,
            AudioLanguage.hy_AM,
            AudioLanguage.az_AZ,
            AudioLanguage.be_BY,
            AudioLanguage.bs_BA,
            AudioLanguage.bg_BG,
            AudioLanguage.ca_ES,
            AudioLanguage.zh_CN,
            AudioLanguage.hr_HR,
            AudioLanguage.cs_CZ,
            AudioLanguage.da_DK,
            AudioLanguage.nl_NL,
            AudioLanguage.en_US,
            AudioLanguage.et_EE,
            AudioLanguage.fi_FI, 
            AudioLanguage.fr_FR, 
            AudioLanguage.gl_ES, 
            AudioLanguage.de_DE, 
            AudioLanguage.el_GR, 
            AudioLanguage.he_IL, 
            AudioLanguage.hi_IN, 
            AudioLanguage.hu_HU, 
            AudioLanguage.is_IS, 
            AudioLanguage.id_ID, 
            AudioLanguage.it_IT, 
            AudioLanguage.ja_JP, 
            AudioLanguage.kn_IN, 
            AudioLanguage.kk_KZ, 
            AudioLanguage.ko_KR, 
            AudioLanguage.lv_LV, 
            AudioLanguage.lt_LT,
            AudioLanguage.mk_MK,
            AudioLanguage.ms_MY,
            AudioLanguage.mr_IN,
            AudioLanguage.ne_NP,
            AudioLanguage.nb_NO,
            AudioLanguage.fa_IR,
            AudioLanguage.pl_PL,
            AudioLanguage.pt_PT,
            AudioLanguage.pt_BR,
            AudioLanguage.ro_RO,
            AudioLanguage.ru_RU,
            AudioLanguage.sr_RS,
            AudioLanguage.sk_SK,
            AudioLanguage.sl_SI,
            AudioLanguage.es_ES,
            AudioLanguage.es_MX,
            AudioLanguage.sw_KE,
            AudioLanguage.sv_SE,
            AudioLanguage.fil_PH,
            AudioLanguage.ta_IN,
            AudioLanguage.ta_LK,
            AudioLanguage.th_TH,
            AudioLanguage.tr_TR,
            AudioLanguage.uk_UA,
            AudioLanguage.ur_PK,
            AudioLanguage.ur_IN,
            AudioLanguage.vi_VN,
            AudioLanguage.cy_GB            
]

class OpenAIVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, name: str, 
                audio_language: cloudlanguagetools.languages.AudioLanguage,
                gender: cloudlanguagetools.constants.Gender):
        self.name = name
        self.gender = gender
        self.audio_language = audio_language
        self.service = cloudlanguagetools.constants.Service.OpenAI
        self.service_fee = cloudlanguagetools.constants.ServiceFee.paid

    def get_voice_key(self):
        return {
            'name': self.name,
            'language': self.audio_language.name            
        }

    def get_voice_shortname(self):
        return self.name

    def get_options(self):
        return VOICE_OPTIONS

class OpenAIService(cloudlanguagetools.service.Service):
    def __init__(self):
        self.chatbot_model = "gpt-3.5-turbo"

    def configure(self, config):
        self.api_key = config['api_key']
        self.client = OpenAI(api_key=self.api_key)

    def single_prompt(self, prompt, max_tokens):
        messages = [
            {'role': 'user', 'content': prompt}
        ]        

        if max_tokens != None:
            response = self.client.chat.completions.create(model=self.chatbot_model,
            messages=messages,
            max_tokens=max_tokens)    
        else:
            response = self.client.chat.completions.create(model=self.chatbot_model,
            messages=messages)    
        logger.debug(pprint.pformat(response))
        tokens_used = response.usage.total_tokens
        response_text = response.choices[0].message.content
        return response_text, tokens_used

    def full_query(self, messages, max_tokens):
        if max_tokens != None:
            response = self.client.chat.completions.create(model=self.chatbot_model,
            messages=messages,
            max_tokens=max_tokens)    
        else:
            response = self.client.chat.completions.create(model=self.chatbot_model,
            messages=messages)    
        logger.debug(pprint.pformat(response))
        return response

    def speech_to_text(self, filepath, audio_format: cloudlanguagetools.options.AudioFormat):

        if audio_format in [cloudlanguagetools.options.AudioFormat.ogg_opus, cloudlanguagetools.options.AudioFormat.ogg_vorbis]:
            # need to convert to wav first
            sound = pydub.AudioSegment.from_ogg(filepath)
            wav_tempfile = tempfile.NamedTemporaryFile(prefix='cloudlanguagetools_OpenAI_speech_to_text', suffix='.wav')
            sound.export(wav_tempfile.name, format="wav")
            filepath = wav_tempfile.name

        logger.debug(f'opening file {filepath}')
        audio_file= open(filepath, "rb")
        transcript = self.client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        return transcript.text
    
    def get_default_model(self, voice_name):
        # these voices don't seem to support tts-1-hd
        if voice_name in ['ballad', 'verse']:
            return DEFAULT_MODEL_GPT_4O
        return DEFAULT_MODEL

    def build_tts_voice_v3(self, voice_name, gender):
        options = VOICE_OPTIONS
        if self.get_default_model(voice_name) == DEFAULT_MODEL_GPT_4O:
            options = copy.deepcopy(options)
            options['model']['values'] = MODELS_GPT_4O_ONLY
            options['model']['default'] = DEFAULT_MODEL_GPT_4O
        return cloudlanguagetools.ttsvoice.TtsVoice_v3(
            name=voice_name,
            voice_key={
                'name': voice_name
            },
            options=options,
            service=cloudlanguagetools.constants.Service.OpenAI,
            gender=gender,
            audio_languages=TTS_SUPPORTED_LANGUAGES,
            service_fee=cloudlanguagetools.constants.ServiceFee.paid
        )

    def get_tts_voice_list_v3(self) -> List[cloudlanguagetools.ttsvoice.TtsVoice_v3]:
        # returns list of TtsVoice_v3

        result = [
            self.build_tts_voice_v3('alloy', cloudlanguagetools.constants.Gender.Female),
            self.build_tts_voice_v3('ash', cloudlanguagetools.constants.Gender.Male),
            # ballad is only available with gpt-4o
            self.build_tts_voice_v3('ballad', cloudlanguagetools.constants.Gender.Male),
            self.build_tts_voice_v3('coral', cloudlanguagetools.constants.Gender.Female),
            self.build_tts_voice_v3('echo', cloudlanguagetools.constants.Gender.Male),
            self.build_tts_voice_v3('fable', cloudlanguagetools.constants.Gender.Female),
            self.build_tts_voice_v3('nova', cloudlanguagetools.constants.Gender.Female),
            self.build_tts_voice_v3('onyx', cloudlanguagetools.constants.Gender.Male),
            self.build_tts_voice_v3('sage', cloudlanguagetools.constants.Gender.Female),
            self.build_tts_voice_v3('shimmer', cloudlanguagetools.constants.Gender.Female),
            self.build_tts_voice_v3('verse', cloudlanguagetools.constants.Gender.Male)
        ]
        return result

    def get_tts_audio(self, text, voice_key, options):
        # https://platform.openai.com/docs/guides/text-to-speech
        # https://platform.openai.com/docs/api-reference/audio/createSpeech?lang=python
        
        output_temp_file = tempfile.NamedTemporaryFile()

        voice_name = voice_key['name']
        speed = options.get('speed', DEFAULT_TTS_SPEED)
        model = options.get('model', self.get_default_model(voice_name))

        response_format_parameter, audio_format = self.get_request_audio_format({
            AudioFormat.mp3: 'mp3',
            AudioFormat.ogg_opus: 'opus',
            AudioFormat.wav: 'wav'
        }, options, AudioFormat.mp3)

        instructions = options.get('instructions', DEFAULT_INSTRUCTIONS)

        audio_parameters = {
            'model': model,
            'voice': voice_name,
            'input': text,
            'response_format': response_format_parameter,
            'speed': speed
        }
        if instructions != DEFAULT_INSTRUCTIONS:
            audio_parameters['instructions'] = instructions

        logger.debug(f'audio_parameters: {pprint.pformat(audio_parameters)}')

        response = self.client.audio.speech.create(
            **audio_parameters,
            timeout=cloudlanguagetools.constants.RequestTimeout
        )
        response.write_to_file(output_temp_file.name)

        return output_temp_file
