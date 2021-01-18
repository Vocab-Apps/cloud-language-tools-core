import requests
import urllib.parse

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.transliterationlanguage

class EasyPronunciationTransliterationLanguage(cloudlanguagetools.transliterationlanguage.TransliterationLanguage):
    def __init__(self, url_path, language, api_params):
        self.service = cloudlanguagetools.constants.Service.EasyPronunciation
        self.url_path = url_path
        self.language = language
        self.api_params = api_params

    def get_transliteration_name(self):
        result = f'{self.language.lang_name} (IPA Pronunciation), {self.service.name}'
        return result

    def get_transliteration_key(self):
        return {
            'url_path': self.url_path,
            'api_params': self.api_params
        }

class EasyPronunciationService(cloudlanguagetools.service.Service):
    def __init__(self):
        self.url_base = 'https://easypronunciation.com'

    def configure(self, access_token):
        self.access_token = access_token

    def get_tts_voice_list(self):
        return []

    def get_translation_language_list(self):
        return []

    def get_transliteration_language_list(self):
        result = [
            EasyPronunciationTransliterationLanguage('/french-api.php', cloudlanguagetools.constants.Language.fr,
            {
                'version': 1,
                'use_un_symbol': 1,
                'vowel_lengthening':1,
                'show_rare_pronunciations':0,
                'french_liaison_styling': 'one_by_one',
                'spell_numbers':1
            })
        ]
        return result

    def get_transliteration(self, text, transliteration_key):
        api_url = self.url_base + transliteration_key['url_path']
        parameters = {
            'access_token': self.access_token,
            'phrase': text
        }
        parameters.update(transliteration_key['api_params'])
        encoded_parameters = urllib.parse.urlencode(parameters)
        full_url = f'{api_url}?{encoded_parameters}'

        # print(f'full_url: {full_url}')

        request = requests.get(full_url)
        result = request.json()


        phonetic_transcription = result['phonetic_transcription']
        result_components = []
        for entry in phonetic_transcription:
            result_components.append(entry['transcriptions'][0])

        return ' '.join(result_components)
