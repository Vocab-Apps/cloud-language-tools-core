import enum
import string
import os
import requests

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.tokenization

class PyThaiNLPTransliterationMode(enum.Enum):
    Romanization = enum.auto()
    IPA = enum.auto()

class PyThaiNLPTokenizationMode(enum.Enum):
    Default = enum.auto()

class PyThaiNLPTransliterationLanguage(cloudlanguagetools.transliterationlanguage.TransliterationLanguage):
    def __init__(self, mode):
        self.language = cloudlanguagetools.languages.Language.th
        self.service = cloudlanguagetools.constants.Service.PyThaiNLP
        self.service_fee = cloudlanguagetools.constants.ServiceFee.free
        self.mode = mode

    def get_transliteration_name(self):
        result = f'{self.language.lang_name} ({self.mode.name}), {self.service.name}'
        return result

    def get_transliteration_shortname(self):
        result = f'{self.mode.name}, {self.service.name}'
        return result        

    def get_transliteration_key(self):
        return {
            'mode': self.mode.name
        }

class PyThaiNLPTokenization(cloudlanguagetools.tokenization.Tokenization):
    def __init__(self, mode):
        self.language = cloudlanguagetools.languages.Language.th
        self.service = cloudlanguagetools.constants.Service.PyThaiNLP
        self.service_fee = cloudlanguagetools.constants.ServiceFee.free
        self.mode = mode

    def get_tokenization_name(self):
        result = f'{self.language.lang_name} ({self.mode.name}), {self.service.name}'
        return result

    def get_tokenization_key(self):
        return {
            'mode': self.mode.name
        }

class PyThaiNLPService(cloudlanguagetools.service.Service):
    BASE_URL = 'https://clt-nlp-api.vocab.ai'

    def __init__(self):
        self.base_url = os.environ.get('PYTHAINLP_URL_OVERRIDE', self.BASE_URL)

    def post_request(self, text, endpoint):
        query_url = self.base_url + endpoint
        response = requests.post(query_url, json={'text': text}, timeout=cloudlanguagetools.constants.RequestTimeout)
        response.raise_for_status()

        response_data = response.json()        
        return response_data

    def get_transliteration_language_list(self):
        result = [
            PyThaiNLPTransliterationLanguage(PyThaiNLPTransliterationMode.Romanization),
            PyThaiNLPTransliterationLanguage(PyThaiNLPTransliterationMode.IPA)
        ]
        return result

    def get_transliteration(self, text, transliteration_key):
        # todo: support IPA
        mode = PyThaiNLPTransliterationMode[transliteration_key['mode']]

        if mode ==  PyThaiNLPTransliterationMode.Romanization:
            return self.post_request(text, '/pythainlp/v1/romanize')
        elif mode == PyThaiNLPTransliterationMode.IPA:
            return self.post_request(text, '/pythainlp/v1/transliterate')

    def get_tokenization(self, text, tokenization_key):
        mode = PyThaiNLPTokenizationMode[tokenization_key['mode']]
        
        if mode == PyThaiNLPTokenizationMode.Default:
            tokens = self.post_request(text, '/pythainlp/v1/word_tokenize')
            tokens = [token for token in tokens if not token.isspace()]
            tokens = [token for token in tokens if not token in string.punctuation]
            token_entries = [{'token': token, 'lemma': token, 'can_translate': True, 'can_transliterate': True} for token in tokens]
            return token_entries

        # raise exception
        raise cloudlanguagetools.errors.RequestError(f'unsupported tokenization mode: {mode.name}')


    def get_tokenization_options(self):
        result = [
            PyThaiNLPTokenization(PyThaiNLPTokenizationMode.Default)
        ]
        return result