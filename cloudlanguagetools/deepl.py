import json
import requests
import tempfile
import logging
import os
import pprint

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.translationlanguage
import cloudlanguagetools.transliterationlanguage
import cloudlanguagetools.errors

logger = logging.getLogger(__name__)

class DeepLTranslationLanguage(cloudlanguagetools.translationlanguage.TranslationLanguage):
    def __init__(self, language, language_id):
        self.service = cloudlanguagetools.constants.Service.DeepL
        self.service_fee = cloudlanguagetools.constants.ServiceFee.paid
        self.language = language
        self.language_id = language_id

    def get_language_id(self):
        return self.language_id


class DeepLService(cloudlanguagetools.service.Service):
    def __init__(self):
        self.base_url = 'https://api.deepl.com/v2/translate'

    def configure(self, config):
        self.api_key = config['key']
    
    def get_tts_voice_list(self):
        return []

    def get_headers(self):
        return {
            'Authorization': f'DeepL-Auth-Key {self.api_key}'
        }

    def get_language_enum(self, deepl_language_code):
        lowercase_str = deepl_language_code.lower()
        override_map = {
            'id': 'id_',
            'zh': 'zh_cn',
            'pt': 'pt_pt'
        }
        lowercase_str = override_map.get(lowercase_str, lowercase_str)
        language = cloudlanguagetools.languages.Language
        return language[lowercase_str]


    def get_translation_language_list(self):
        language = cloudlanguagetools.languages.Language
        url = 'https://api.deepl.com/v2/languages'
        response = requests.get(url, headers=self.get_headers(), timeout=cloudlanguagetools.constants.RequestTimeout)
        response.raise_for_status()
        # pprint.pprint(response.json())
        results = []
        for language_entry in response.json():
            try:
                # pprint.pprint(language_entry)
                deepl_language_code = language_entry['language']
                language_enum = self.get_language_enum(deepl_language_code)
                results.append(DeepLTranslationLanguage(language_enum, deepl_language_code))
                # if it's portuguese, replicate the entry for PT-PT and PT-BR
                if language_enum == language.pt_pt:
                    results.append(DeepLTranslationLanguage(language.pt_br, deepl_language_code))
            except Exception as e:
                logger.exception(f'could not process Deepl language entry: {language_entry}')
        return results

    def get_tts_voice_list(self):
        result = []
        return result


    def get_transliteration_language_list(self):
        return []

    def get_translation(self, text, from_language_key, to_language_key):

        override_source_language_map = {
            'PT-PT': 'PT',
            'PT-BR': 'PT'
        }
        from_language_key = override_source_language_map.get(from_language_key, from_language_key)


        params = {
            'auth_key': self.api_key,
            'text': text,
            'source_lang': from_language_key,
            'target_lang': to_language_key
        }
        response = requests.get(self.base_url, params=params, timeout=cloudlanguagetools.constants.RequestTimeout)

        if response.status_code == 200:
            # {'translations': [{'translation': 'Le coût est très bas.'}], 'word_count': 2, 'character_count': 4}
            data = response.json()
            return data['translations'][0]['text']

        error_message = error_message = f'DeepL: could not translate text [{text}] from {from_language_key} to {to_language_key} (status_code: {response.status_code} {response.content})'
        raise cloudlanguagetools.errors.RequestError(error_message)