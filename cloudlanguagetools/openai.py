from openai import OpenAI

import logging
import tempfile
import pydub
import pprint
from typing import List

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.options

from cloudlanguagetools.languages import AudioLanguage

logger = logging.getLogger(__name__)

DEFAULT_TTS_SPEED = 1.0

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
        return {
            'speed' : {
                'type': cloudlanguagetools.options.ParameterType.number.name,
                'min': 0.25,
                'max': 4.0,
                'default': DEFAULT_TTS_SPEED
            },
            cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER: {
                'type': cloudlanguagetools.options.ParameterType.list.name,
                'values': [
                    cloudlanguagetools.options.AudioFormat.mp3.name,
                    cloudlanguagetools.options.AudioFormat.ogg_opus.name,
                ],
                'default': cloudlanguagetools.options.AudioFormat.mp3.name
            }
        }

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
    
    
    def get_tts_voice_list(self) -> List[OpenAIVoice]:
        result = []

        supported_languages = [
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
            # AudioLanguage.tl_PH, # need to add tagalog language in AudioLanguages
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

        for audio_language in supported_languages:
            result.extend([
                OpenAIVoice('alloy', audio_language, cloudlanguagetools.constants.Gender.Female),
                OpenAIVoice('echo', audio_language, cloudlanguagetools.constants.Gender.Male),
                OpenAIVoice('fable', audio_language, cloudlanguagetools.constants.Gender.Female),
                OpenAIVoice('onyx', audio_language, cloudlanguagetools.constants.Gender.Male),
                OpenAIVoice('nova', audio_language, cloudlanguagetools.constants.Gender.Female),
                OpenAIVoice('shimmer', audio_language, cloudlanguagetools.constants.Gender.Female),
            ])
        return result

    def get_tts_audio(self, text, voice_key, options):
        # https://platform.openai.com/docs/guides/text-to-speech
        # https://platform.openai.com/docs/api-reference/audio/createSpeech?lang=python
        
        output_temp_file = tempfile.NamedTemporaryFile()

        speed = options.get('speed', DEFAULT_TTS_SPEED)
        response_format = options.get(cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER, 
            cloudlanguagetools.options.AudioFormat.mp3.name)
        if response_format == cloudlanguagetools.options.AudioFormat.ogg_opus.name:
            response_format = 'opus'

        response = self.client.audio.speech.create(
            model='tts-1-hd',
            voice=voice_key['name'],
            input=text,
            response_format=response_format,
            speed=speed
        )
        response.stream_to_file(output_temp_file.name)

        return output_temp_file
