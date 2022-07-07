import json
import requests
import tempfile
import logging
import os

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.translationlanguage
import cloudlanguagetools.transliterationlanguage
import cloudlanguagetools.errors


class DeepLTranslationLanguage(cloudlanguagetools.translationlanguage.TranslationLanguage):
    def __init__(self, language, language_id):
        self.service = cloudlanguagetools.constants.Service.DeepL
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


    def get_translation_language_list(self):
        language = cloudlanguagetools.languages.Language
        result = [
            DeepLTranslationLanguage(language.bg, 'BG'),
            DeepLTranslationLanguage(language.cs, 'CS'),
            DeepLTranslationLanguage(language.da, 'DA'),
            DeepLTranslationLanguage(language.de, 'DE'),
            DeepLTranslationLanguage(language.el, 'EL'),
            DeepLTranslationLanguage(language.en, 'EN'),
            DeepLTranslationLanguage(language.es, 'ES'),
            DeepLTranslationLanguage(language.et, 'ET'),
            DeepLTranslationLanguage(language.fi, 'FI'),
            DeepLTranslationLanguage(language.fr, 'FR'),
            DeepLTranslationLanguage(language.hu, 'HU'),
            DeepLTranslationLanguage(language.it, 'IT'),
            DeepLTranslationLanguage(language.ja, 'JA'),
            DeepLTranslationLanguage(language.lt, 'LT'),
            DeepLTranslationLanguage(language.lv, 'LV'),
            DeepLTranslationLanguage(language.nl, 'NL'),
            DeepLTranslationLanguage(language.pl, 'PL'),
            DeepLTranslationLanguage(language.pt_pt, 'PT'),
            DeepLTranslationLanguage(language.ro, 'RO'),
            DeepLTranslationLanguage(language.ru, 'RU'),
            DeepLTranslationLanguage(language.sk, 'SK'),
            DeepLTranslationLanguage(language.sl, 'SL'),
            DeepLTranslationLanguage(language.sv, 'SV'),
            DeepLTranslationLanguage(language.zh_cn, 'ZH'),
        ]
        return result        


    def get_tts_voice_list(self):
        result = []
        return result


    def get_transliteration_language_list(self):
        return []

    def get_translation(self, text, from_language_key, to_language_key):
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