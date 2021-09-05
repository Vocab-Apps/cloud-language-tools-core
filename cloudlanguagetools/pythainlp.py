import pythainlp

import cloudlanguagetools.service
import cloudlanguagetools.constants


class PyThaiNLPTransliterationLanguage(cloudlanguagetools.transliterationlanguage.TransliterationLanguage):
    def __init__(self, engine, description):
        self.language = cloudlanguagetools.constants.Language.th
        self.service = cloudlanguagetools.constants.Service.PyThaiNLP
        self.engine = engine
        self.description = description

    def get_transliteration_name(self):
        result = f'{self.language.lang_name} ({self.description}), {self.service.name}'
        return result

    def get_transliteration_key(self):
        return {
            'engine': self.engine
        }

class PyThaiNLPService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def get_transliteration_language_list(self):
        result = [
            PyThaiNLPTransliterationLanguage('thai2rom', 'Romanization')
        ]
        return result

    def get_transliteration(self, text, transliteration_key):
        # todo: support IPA
        engine = transliteration_key['engine']
        return pythainlp.romanize(text, engine=engine)

    def tokenize(self, text, tokenization_key):
        tokens = pythainlp.word_tokenize(text)
        return tokens