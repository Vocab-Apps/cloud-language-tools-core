import json
import requests
import tempfile
import logging
import os
import pprint

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.translationlanguage
import cloudlanguagetools.transliterationlanguage
import cloudlanguagetools.errors


class ForvoVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, voice_data):
        # print(voice_data)
        self.service = cloudlanguagetools.constants.Service.Forvo
        locale = voice_data['Locale']
        language_enum_name = locale.replace('-', '_')
        self.audio_language = cloudlanguagetools.constants.AudioLanguage[language_enum_name]
        self.name = voice_data['Name']
        self.display_name = voice_data['DisplayName']
        self.local_name = voice_data['LocalName']
        self.short_name = voice_data['ShortName']
        self.gender = cloudlanguagetools.constants.Gender[voice_data['Gender']]

        self.locale = locale
        self.voice_type = voice_data['VoiceType']


    def get_voice_key(self):
        return {
            'name': self.name
        }

    def get_voice_shortname(self):
        if self.local_name != self.display_name:
            return f'{self.display_name} {self.local_name} ({self.voice_type})'
        else:
            return f'{self.display_name} ({self.voice_type})'

    def get_options(self):
        return {
            'rate' : {
                'type': 'number',
                'min': 0.5,
                'max': 3.0,
                'default': 1.0
            },
            'pitch': {
                'type': 'number',
                'min': -100,
                'max': 100,
                'default': 0
            }
        }

def get_translation_language_enum(language_id):
    forvo_language_id_map = {
        # 'as': 'as_',
        # 'fr-ca': 'fr_ca',
        # 'fr-CA': 'fr_ca',
        # 'id': 'id_',
        # 'is': 'is_',
        # 'or': 'or_',
        # 'pt': 'pt_br',
        # 'pt-pt': 'pt_pt',
        # 'pt-PT': 'pt_pt',
        # 'sr-Cyrl': 'sr_cyrl',
        # 'sr-Latn': 'sr_latn',
        # 'tlh-Latn': 'tlh_latn',
        # 'tlh-Piqd': 'tlh_piqd',
        # 'zh-Hans': 'zh_cn',
        # 'zh-Hant': 'zh_tw'
        'zh': 'zh_cn',
        'ind': 'id_'
    }
    if language_id in forvo_language_id_map:
        language_id = forvo_language_id_map[language_id]
    return cloudlanguagetools.constants.Language[language_id]


class ForvoService(cloudlanguagetools.service.Service):
    def __init__(self):
        self.url_base = 'https://apicommercial.forvo.com'

    def configure(self):
        self.key = os.environ['FORVO_KEY']

    def get_headers(self):
        # forvo uses cloudflare or something equivalent
        return {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0'}

    def get_tts_audio(self, text, voice_key, options):
        output_temp_file = tempfile.NamedTemporaryFile()
        output_temp_filename = output_temp_file.name
        speech_config = Forvo.cognitiveservices.speech.SpeechConfig(subscription=self.key, region=self.region)
        speech_config.set_speech_synthesis_output_format(Forvo.cognitiveservices.speech.SpeechSynthesisOutputFormat["Audio24Khz96KBitRateMonoMp3"])
        audio_config = Forvo.cognitiveservices.speech.audio.AudioOutputConfig(filename=output_temp_filename)
        synthesizer = Forvo.cognitiveservices.speech.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

        pitch = options.get('pitch', 0)
        pitch_str = f'{pitch:+.0f}Hz'
        rate = options.get('rate', 1.0)
        rate_str = f'{rate:0.1f}'

        ssml_str = f"""<speak version="1.0" xmlns="https://www.w3.org/2001/10/synthesis" xml:lang="en-US">
  <voice name="{voice_key['name']}">
    <prosody pitch="{pitch_str}" rate="{rate_str}" >
        {text}
    </prosody>
  </voice>
</speak>"""

        # print(ssml_str)

        result = synthesizer.start_speaking_ssml(ssml_str)

        return output_temp_file

    def get_tts_voice_list(self):
        # returns list of TtSVoice

        url = f'{self.url_base}/key/{self.key}/format/json/action/language-list/min-pronunciations/5000'
        response = requests.get(url, headers=self.get_headers())
        if response.status_code == 200:
            data = response.json()
            languages = data['items']
            for language in languages:
                try:
                    language_id = language['code']
                    language_enum = get_translation_language_enum(language_id)
                    logging.info(f'language: {language_id}: {language_enum}')
                except KeyError:
                    logging.error(f'forvo language mapping not found: {language}')

            # pprint.pprint(data)
        else:
            print(response.content)

        return []


    def get_translation_language_list(self):
        result = []
        return result

    def get_transliteration_language_list(self):
        result = []
        return result


    