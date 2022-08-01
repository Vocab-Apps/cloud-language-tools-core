import abc
import json

class DictionaryLookup(abc.ABC):
    def __init__(self):
        pass

    def get_language_code(self):
        return self.language.name

    def get_language_name(self):
        return self.language.lang_name

    def get_target_language_code(self):
        return self.target_language.name

    def get_target_language_name(self):
        return self.target_language.lang_name

    @abc.abstractmethod
    def get_lookup_name(self):
        pass

    @abc.abstractmethod
    def get_lookup_shortname(self):
        pass

    @abc.abstractmethod
    def get_lookup_key(self):
        pass    

    def get_lookup_id(self):
        return json.dumps({
            'service': self.service.name,
            'key': self.get_lookup_key()
        })

    def json_obj(self):
        return {
            'service': self.service.name,
            'language_code': self.get_language_code(),
            'language_name': self.get_language_name(),
            'lookup_name': self.get_lookup_name(),
            'lookup_shortname': self.get_lookup_shortname(),
            'lookup_key': self.get_lookup_key(),
            'lookup_id': self.get_lookup_id()
        } 