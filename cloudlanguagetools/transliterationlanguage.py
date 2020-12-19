
class TransliterationLanguage():
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
            'transliteration_name': self.get_transliteration_name(),
            'transliteration_key': self.get_transliteration_key()
        } 