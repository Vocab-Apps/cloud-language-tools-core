import logging
import requests
import os

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.tokenization

logger = logging.getLogger(__name__)

class SpacyTokenization(cloudlanguagetools.tokenization.Tokenization):
    def __init__(self, language, model_name, variant=None):
        self.language = language
        self.service = cloudlanguagetools.constants.Service.Spacy
        self.service_fee = cloudlanguagetools.constants.ServiceFee.free
        self.model_name = model_name
        self.variant = variant

    def get_tokenization_name(self):
        if self.variant != None:
            result = f'{self.language.lang_name} ({self.variant}), {self.service.name}'
        else:
            result = f'{self.language.lang_name}, {self.service.name}'
        return result

    def get_tokenization_key(self):
        return {
            'model_name': self.model_name
        }

class SpacyService(cloudlanguagetools.service.Service):
    BASE_URL = 'https://clt-nlp-api.vocab.ai'

    def __init__(self):
        self.BASE_URL = os.environ.get('SPACY_URL_OVERRIDE', self.BASE_URL)

    def get_tokenization(self, text, tokenization_key):
        model_name = tokenization_key['model_name']

        query_url = self.BASE_URL + '/spacy/v1/tokenize'
        response = requests.post(query_url, json={'language': model_name, 'text': text}, timeout=cloudlanguagetools.constants.RequestTimeout)
        response_data = response.json()        

        if response.status_code == 200:
            return response_data

        # raise exception
        raise cloudlanguagetools.errors.RequestError(f'could not generate tokenization model_name {model_name} text: {text}: {response}')


    def get_tokenization_options(self):
        result = [
            SpacyTokenization(cloudlanguagetools.languages.Language.en, 'en'),
            SpacyTokenization(cloudlanguagetools.languages.Language.fr, 'fr'),
            SpacyTokenization(cloudlanguagetools.languages.Language.ja, 'ja'),
            SpacyTokenization(cloudlanguagetools.languages.Language.de, 'de'),
            SpacyTokenization(cloudlanguagetools.languages.Language.es, 'es'),
            SpacyTokenization(cloudlanguagetools.languages.Language.ru, 'ru'),
            SpacyTokenization(cloudlanguagetools.languages.Language.pl, 'pl'),
            SpacyTokenization(cloudlanguagetools.languages.Language.it, 'it'),

        ]
        chinese_language_list = [
            cloudlanguagetools.languages.Language.zh_cn,
            cloudlanguagetools.languages.Language.zh_tw,
            cloudlanguagetools.languages.Language.yue
        ]
        for language in chinese_language_list:
            # chinese variants
            result.extend([
                SpacyTokenization(language, 'zh_jieba', 'Jieba (words)'),
                SpacyTokenization(language, 'zh_char', 'Characters'),
                SpacyTokenization(language, 'zh_pkuseg', 'PKUSeg (words)')
            ])
        return result