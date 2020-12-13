import os
import tempfile
import google.cloud.texttospeech
import google.cloud.translate_v2
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

def get_translation_language_enum(language_id):
    google_language_id_map = {
        'as': 'as_',
        'fr-ca': 'fr_ca',
        'id': 'id_',
        'is': 'is_',
        'or': 'or_',
        'pt': 'pt_br',
        'pt-pt': 'pt_pt',
        'sr-Cyrl': 'sr_cyrl',
        'sr-Latn': 'sr_latn',
        'tlh-Latn': 'tlh_latn',
        'tlh-Piqd': 'tlh_piqd',
        'zh-CN': 'zh_cn',
        'zh-TW': 'zh_tw',
        'zh': 'zh_cn'
    }
    if language_id in google_language_id_map:
        language_id = google_language_id_map[language_id]
    return cloudlanguagetools.constants.Language[language_id]

class GoogleTranslationLanguage(cloudlanguagetools.translationlanguage.TranslationLanguage):
    def __init__(self, language_id):
        self.service = cloudlanguagetools.constants.Service.Google
        self.language_id = language_id
        self.language = get_translation_language_enum(language_id)

    def get_language_id(self):
        return self.language_id

class GoogleService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def configure(self):
        pass

    def get_client(self):
        client = google.cloud.texttospeech.TextToSpeechClient()
        return client

    def get_translation_client(self):
        translate_client = google.cloud.translate_v2.Client()
        return translate_client

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

    def get_translation_language_list(self):
        data = self.get_translation_languages()
        result_dict = {}
        for entry in data:
            translation_language = GoogleTranslationLanguage(entry['language'])
            result_dict[translation_language.get_language_code()] = translation_language
        return result_dict.values()


    def get_translation(self, text, from_language_key, to_language_key):
        client = self.get_translation_client()
        result = client.translate(text, source_language=from_language_key, target_language=to_language_key)
        return result["translatedText"]

    def get_translation_languages(self):
        translate_client = google.cloud.translate_v2.Client()

        results = translate_client.get_languages()

        return results

    def detect_language(self, input_text):
        client = self.get_translation_client()

        # Text can also be a sequence of strings, in which case this method
        # will return a sequence of results for each text.
        result = client.detect_language(input_text)

        print("Text: {}".format(input_text))
        print("Confidence: {}".format(result["confidence"]))
        print("Language: {}".format(result["language"]))