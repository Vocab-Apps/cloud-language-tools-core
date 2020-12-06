import os
import tempfile
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
        self.google_ssml_gender = google.cloud.texttospeech.SsmlVoiceGender(voice_data.ssml_gender)
        gender_str = self.google_ssml_gender.name.lower().capitalize()
        self.gender = cloudlanguagetools.constants.Gender[gender_str]
        assert len(voice_data.language_codes) == 1
        self.google_language_code = voice_data.language_codes[0]
        self.language = language_code_to_enum(self.google_language_code)


    def get_voice_key(self):
        return {
            'name': self.name,
            'language_code': self.google_language_code,
            'ssml_gender': self.google_ssml_gender.name
        }



class GoogleService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def configure(self):
        #self.cache_voice_list()
        pass

    def get_client(self):
        client = google.cloud.texttospeech.TextToSpeechClient()
        return client

    def get_tts_audio(self, text, voice_key, options):
        client = self.get_client()

        input_text = google.cloud.texttospeech.SynthesisInput(text=text)

        # Note: the voice can also be specified by name.
        # Names of voices can be retrieved with client.list_voices().
        voice = google.cloud.texttospeech.VoiceSelectionParams(
            name=voice_key['name'],
            language_code=voice_key['language_code'],
            ssml_gender=google.cloud.texttospeech.SsmlVoiceGender[voice_key['ssml_gender']]
        )

        audio_config = google.cloud.texttospeech.AudioConfig(
            audio_encoding=google.cloud.texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            request={"input": input_text, "voice": voice, "audio_config": audio_config}
        )

        # The response's audio_content is binary.
        output_temp_file = tempfile.NamedTemporaryFile()
        output_temp_filename = output_temp_file.name        
        with open(output_temp_filename, "wb") as out:
            out.write(response.audio_content)

        return output_temp_file


    def get_tts_voice_list(self):
        client = self.get_client()

        # Performs the list voices request
        voices = client.list_voices()

        result = []

        for voice in voices.voices:
            result.append(GoogleVoice(voice))

        return result

    def cache_voice_list(self):
        # we need to have a cache in order to properly process tts audio requests
        voice_list = self.get_tts_voice_list()
        self.voice_map = {}
        for voice in voice_list:
            self.voice_map[voice.get_voice_id()] = voice

        