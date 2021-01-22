import json
import requests

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.translationlanguage
import cloudlanguagetools.transliterationlanguage
import cloudlanguagetools.errors

def get_translation_language_enum(language_id):
    # print(f'language_id: {language_id}')
    watson_language_id_map = {
        'fr-CA': 'fr_ca',
        'id': 'id_',
        'pt': 'pt_pt',
        'sr': 'sr_cyrl',
        'zh':'zh_cn',
        'zh-TW': 'zh_tw'

    }
    if language_id in watson_language_id_map:
        language_id = watson_language_id_map[language_id]
    return cloudlanguagetools.constants.Language[language_id]

class WatsonTranslationLanguage(cloudlanguagetools.translationlanguage.TranslationLanguage):
    def __init__(self, language_id):
        self.service = cloudlanguagetools.constants.Service.Watson
        self.language_id = language_id
        self.language = get_translation_language_enum(language_id)

    def get_language_id(self):
        return self.language_id

class WatsonService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def configure(self, key, url):
        self.key = key
        self.url = url
    
    def get_tts_voice_list(self):
        return []

    def get_translation_languages(self):
        response = requests.get(self.url + '/v3/languages?version=2018-05-01', auth=('apikey', self.key))
        return response.json()

    def get_translation_language_list(self):
        language_list = self.get_translation_languages()['languages']
        result = []
        # print(language_list)
        for entry in language_list:
            if entry['supported_as_source'] == True and entry['supported_as_target'] == True:
                # print(entry)
                language_id = entry['language']
                result.append(WatsonTranslationLanguage(language_id))
        return result        