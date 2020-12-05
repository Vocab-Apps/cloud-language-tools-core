
class TtsVoice():
    def __init__(self):
        pass

    def get_gender(self):
        return self.gender
    
    def get_language(self):
        return self.language

    def json_obj(self):
        return {
            'service': self.service.name,
            'gender': self.get_gender().name,
            'language': self.get_language().name,
            'voice_id': self.get_voice_id()
        }
   
