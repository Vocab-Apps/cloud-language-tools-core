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

GENDER_MAP = {
    cloudlanguagetools.constants.Gender.Male: 'm',
    cloudlanguagetools.constants.Gender.Female: 'f'
}

class ForvoVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, language_code, country_code, audio_language, gender):
        # print(voice_data)
        self.service = cloudlanguagetools.constants.Service.Forvo
        self.language_code = language_code
        self.country_code = country_code
        self.audio_language = audio_language
        self.gender = gender

    def get_voice_key(self):
        result = {
            'language_code': self.language_code,
            'country_code': self.country_code
        }
        if self.gender != cloudlanguagetools.constants.Gender.Any:
            result['gender'] = GENDER_MAP[self.gender]
        return result

    def get_voice_description(self):
        return f'{self.get_audio_language_name()}, {self.get_gender().name}, {self.service.name}'

    def get_options(self):
        return {}



class ForvoService(cloudlanguagetools.service.Service):
    def __init__(self):
        self.url_base = 'https://apicommercial.forvo.com'
        self.build_audio_language_map()

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

    def get_language_enum(self, language_id):
        forvo_language_id_map = {
            'zh': 'zh_cn',
            'ind': 'id_',
            'pt': 'pt_pt'
        }
        if language_id in forvo_language_id_map:
            language_id = forvo_language_id_map[language_id]
        return cloudlanguagetools.constants.Language[language_id]

    def get_audio_language_enum(self, language_id):
        pass

    def get_voices_for_language_entry(self, language):
        try:
            language_code = language['code']
            language_enum = self.get_language_enum(language_code)
            # create as many voices as there are audio languages available

            audio_language_list = self.audio_language_map[language_enum]
            logging.info(f'language: {language_enum} audio_language: {audio_language_list}')
            
            voices = []

            for gender in cloudlanguagetools.constants.Gender:
                if len(audio_language_list) == 1:
                    country_code = 'ANY'
                    voices.append(ForvoVoice(language_code, country_code, audio_language_list[0], gender))

            return voices

        except KeyError:
            logging.error(f'forvo language mapping not found: {language}')

        return []

    def build_audio_language_map(self):
        self.audio_language_map = {}
        for audio_language in cloudlanguagetools.constants.AudioLanguage:
            language = audio_language.lang
            if language not in self.audio_language_map:
                self.audio_language_map[language] = []
            self.audio_language_map[language].append(audio_language)
            

    def get_tts_voice_list(self):
        # returns list of TtSVoice

        voice_list = []

        url = f'{self.url_base}/key/{self.key}/format/json/action/language-list/min-pronunciations/5000'
        response = requests.get(url, headers=self.get_headers())
        if response.status_code == 200:
            data = response.json()
            languages = data['items']
            for language in languages:
                voice_list.extend(self.get_voices_for_language_entry(language))

            # pprint.pprint(data)
        else:
            print(response.content)

        return voice_list


    def get_translation_language_list(self):
        result = []
        return result

    def get_transliteration_language_list(self):
        result = []
        return result


    