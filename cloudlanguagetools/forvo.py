import json
import requests
import urllib
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

COUNTRY_ANY = 'ANY'

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

        language = voice_key['language_code']

        sex_param = ''
        if 'gender' in voice_key:
            sex_param = f"/sex/{voice_key['gender']}"
        
        country_code = ''
        if voice_key['country_code'] != COUNTRY_ANY:
            # user selected a particular country
            country_code = f"/country/{voice_key['country_code']}"

        username_param = ''
        if 'preferred_user' in voice_key:
            username_param = f"/username/{voice_key['preferred_user']}"

        encoded_text = urllib.parse.quote(text)

        url = f'{self.url_base}/key/{self.key}/format/json/action/word-pronunciations/word/{encoded_text}/language/{language}{sex_param}{username_param}/order/rate-desc/limit/1{country_code}'

        response = requests.get(url, headers=self.get_headers(), timeout=cloudlanguagetools.constants.RequestTimeout)
        if response.status_code == 200:
            data = response.json()
            items = data['items']
            if len(items) == 0:
                error_message = f"Pronunciation not found in Forvo for word [{text}], language={language}, country={voice_key['country_code']}"
                raise cloudlanguagetools.errors.NotFoundError(error_message)
            audio_url = items[0]['pathmp3']
            output_temp_file = tempfile.NamedTemporaryFile()
            output_temp_filename = output_temp_file.name
            audio_request = requests.get(audio_url, headers=self.get_headers(), timeout=cloudlanguagetools.constants.RequestTimeout)
            open(output_temp_filename, 'wb').write(audio_request.content)
            return output_temp_file
        else:
            error_message = f'status_code: {response.status_code} response: {response.content}'
            raise cloudlanguagetools.errors.RequestError(error_message)


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

    def get_country_code(self, audio_language):
        country_code_map = {
            cloudlanguagetools.constants.AudioLanguage.fr_FR: 'FRA',
            cloudlanguagetools.constants.AudioLanguage.fr_CH: 'CHE',
            cloudlanguagetools.constants.AudioLanguage.fr_BE: 'BEL',
            cloudlanguagetools.constants.AudioLanguage.nl_BE: 'BEL',
            cloudlanguagetools.constants.AudioLanguage.nl_NL: 'NLD',
            cloudlanguagetools.constants.AudioLanguage.ar_EG: 'EGY',
            cloudlanguagetools.constants.AudioLanguage.ar_SA: 'SAU',
            cloudlanguagetools.constants.AudioLanguage.ar_XA: 'ANY', # any country
            cloudlanguagetools.constants.AudioLanguage.de_AT: 'AUT',
            cloudlanguagetools.constants.AudioLanguage.de_DE: 'DEU',
            cloudlanguagetools.constants.AudioLanguage.de_CH: 'CHE',
            cloudlanguagetools.constants.AudioLanguage.en_AU: 'AUS',
            cloudlanguagetools.constants.AudioLanguage.en_CA: 'CAN',
            cloudlanguagetools.constants.AudioLanguage.en_GB: 'GBR',
            cloudlanguagetools.constants.AudioLanguage.en_IE: 'IRL',
            cloudlanguagetools.constants.AudioLanguage.en_IN: 'IND',
            cloudlanguagetools.constants.AudioLanguage.en_US: 'USA',
            cloudlanguagetools.constants.AudioLanguage.es_ES: 'ESP',
            cloudlanguagetools.constants.AudioLanguage.es_MX: 'MEX',
            cloudlanguagetools.constants.AudioLanguage.es_LA: 'ANY', # any country
            cloudlanguagetools.constants.AudioLanguage.es_US: 'USA', 
            cloudlanguagetools.constants.AudioLanguage.en_GB_WLS: 'GBR', 
        }
        if audio_language not in country_code_map:
            logging.error(f'no country code found for {audio_language}')
        return country_code_map[audio_language]

    def get_voices_for_language_entry(self, language):
        try:
            language_code = language['code']
            language_enum = self.get_language_enum(language_code)
            # create as many voices as there are audio languages available

            audio_language_list = self.audio_language_map[language_enum]
            
            voices = []

            for gender in cloudlanguagetools.constants.Gender:
                if len(audio_language_list) == 1:
                    country_code = COUNTRY_ANY
                    voices.append(ForvoVoice(language_code, country_code, audio_language_list[0], gender))
                else:
                    # logging.info(f'multiple audio languages found: {audio_language_list}')
                    for audio_language in audio_language_list:
                        country_code = self.get_country_code(audio_language)
                        voices.append(ForvoVoice(language_code, country_code, audio_language, gender))

            return voices

        except KeyError:
            logging.warn(f'forvo language mapping not found: {language}')

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
        response = requests.get(url, headers=self.get_headers(), timeout=cloudlanguagetools.constants.RequestTimeout)
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


    