import google.cloud.texttospeech
import cloudlanguagetools.service
import cloudlanguagetools.constants

def language_code_to_enum(language_code):
    override_map = {
        'cmn-TW': cloudlanguagetools.constants.Language.zh_TW,
        'cmn-CN': cloudlanguagetools.constants.Language.zh_CN,
        'yue-HK': cloudlanguagetools.constants.Language.zh_HK
    }
    if language_code in override_map:
        return override_map[language_code]
    language_enum_name = language_code.replace('-', '_')
    return cloudlanguagetools.constants.Language[language_enum_name]

class GoogleVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, voice_data):
        self.service = cloudlanguagetools.constants.Service.Google
        self.name = voice_data.name
        print(self.name)
        gender_str = google.cloud.texttospeech.SsmlVoiceGender(voice_data.ssml_gender).name.lower().capitalize()
        self.gender = cloudlanguagetools.constants.Gender[gender_str]
        assert len(voice_data.language_codes) == 1
        language_code = voice_data.language_codes[0]
        self.language = language_code_to_enum(language_code)

    def get_voice_id(self):
        return self.name


class GoogleService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def get_tts_voice_list(self):
        print('google.get_tts_voice_list')
        client = google.cloud.texttospeech.TextToSpeechClient()

        # Performs the list voices request
        voices = client.list_voices()

        result = []

        for voice in voices.voices:
            result.append(GoogleVoice(voice))

        return result

        