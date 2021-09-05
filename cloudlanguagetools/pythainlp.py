import pythainlp
import enum

import cloudlanguagetools.service
import cloudlanguagetools.constants

class PyThaiNLPTransliterationMode(enum.Enum):
    Romanization = enum.auto()
    IPA = enum.auto()

class PyThaiNLPTransliterationLanguage(cloudlanguagetools.transliterationlanguage.TransliterationLanguage):
    def __init__(self, mode):
        self.language = cloudlanguagetools.constants.Language.th
        self.service = cloudlanguagetools.constants.Service.PyThaiNLP
        self.mode = mode

    def get_transliteration_name(self):
        result = f'{self.language.lang_name} ({self.mode.name}), {self.service.name}'
        return result

    def get_transliteration_key(self):
        return {
            'mode': self.mode.name
        }

class PyThaiNLPService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

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
            return pythainlp.romanize(text, engine='thai2rom')
        elif mode == PyThaiNLPTransliterationMode.IPA:
            return pythainlp.transliterate(text)

    def tokenize(self, text, tokenization_key):
        tokens = pythainlp.word_tokenize(text)
        return tokens