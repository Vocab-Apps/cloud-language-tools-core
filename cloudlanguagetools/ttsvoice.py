
class TtsVoice():
    def __init__(self):
        pass

    def get_gender(self):
        return self.gender

    def get_language_code(self):
        return self.audio_language.lang.name

    def get_audio_language_code(self):
        return self.audio_language.name

    def get_audio_language_name(self):
        return self.audio_language.audio_lang_name

    def get_voice_description(self):
        return f'{self.get_audio_language_name()}, {self.get_gender().name}, {self.get_voice_shortname()}, {self.service.name}'

    def json_obj(self):
        return {
            'service': self.service.name,
            'gender': self.get_gender().name,
            'language_code': self.get_language_code(),
            'audio_language_code': self.get_audio_language_code(),
            'audio_language_name': self.get_audio_language_name(),
            'voice_key': self.get_voice_key(),
            'voice_description': self.get_voice_description(),
            'voice_name': self.get_voice_shortname(),
            'options': self.get_options()
        }
   
