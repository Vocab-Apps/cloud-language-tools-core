import abc
import json

class TransliterationLanguage(abc.ABC):
    def __init__(self):
        pass

    def get_language_code(self):
        return self.language.name

    def get_language_name(self):
        return self.language.lang_name

    @abc.abstractmethod
    def get_transliteration_name(self):
        pass

    @abc.abstractmethod
    def get_transliteration_shortname(self):
        pass

    @abc.abstractmethod
    def get_transliteration_key(self):
        pass    

    def get_transliteration_id(self):
        return json.dumps({
            'service': self.service.name,
            'key': self.get_transliteration_key()
        })

    def json_obj(self):
        return {
            'service': self.service.name,
            'language_code': self.get_language_code(),
            'language_name': self.get_language_name(),
            'transliteration_name': self.get_transliteration_name(),
            'transliteration_shortname': self.get_transliteration_shortname(),
            'transliteration_key': self.get_transliteration_key(),
            'transliteration_id': self.get_transliteration_id()
        } 