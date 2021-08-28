import pythainlp

import cloudlanguagetools.service


class PyThaiNLPService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def get_transliteration(self, text, transliteration_key):
        # todo: support IPA
        return pythainlp.romanize(text, engine="thai2rom")

    def tokenize(self, text, tokenization_key):
        tokens = pythainlp.word_tokenize(text)
        return tokens