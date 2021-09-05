
class Tokenization():
    def __init__(self):
        pass

    def get_language_code(self):
        return self.language.name

    def get_language_name(self):
        return self.language.lang_name

    def json_obj(self):
        return {
            'service': self.service.name,
            'language_code': self.get_language_code(),
            'language_name': self.get_language_name(),
            'tokenization_name': self.get_tokenization_name(),
            'tokenization_key': self.get_tokenization_key()
        } 