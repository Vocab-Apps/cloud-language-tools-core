
class TtsVoice():
    def __init__(self):
        pass

    def get_gender(self):
        return self.gender
    
    def get_language_code(self):
        return self.language.name

    def get_language_name(self):
        return self.language.lang_name

    def json_obj(self):
        return {
            'service': self.service.name,
            'gender': self.get_gender().name,
            'language_code': self.get_language_code(),
            'language_name': self.get_language_name(),
            'voice_key': self.get_voice_key()
        }
   
