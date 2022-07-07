import os
import tempfile
import html
import base64
import logging
import google.cloud.texttospeech
import google.cloud.translate_v2
import google.api_core.exceptions
import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.options
import cloudlanguagetools.languages

def language_code_to_enum(language_code):
    override_map = {
        'cmn-TW': cloudlanguagetools.languages.AudioLanguage.zh_TW,
        'cmn-CN': cloudlanguagetools.languages.AudioLanguage.zh_CN,
        'yue-HK': cloudlanguagetools.languages.AudioLanguage.zh_HK
    }
    if language_code in override_map:
        return override_map[language_code]
    language_enum_name = language_code.replace('-', '_')
    return cloudlanguagetools.languages.AudioLanguage[language_enum_name]

class GoogleVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, voice_data):
        self.service = cloudlanguagetools.constants.Service.Google
        self.name = voice_data.name
        self.google_ssml_gender = google.cloud.texttospeech.SsmlVoiceGender(voice_data.ssml_gender)
        gender_str = self.google_ssml_gender.name.lower().capitalize()
        self.gender = cloudlanguagetools.constants.Gender[gender_str]
        assert len(voice_data.language_codes) == 1
        self.google_language_code = voice_data.language_codes[0]
        self.audio_language = language_code_to_enum(self.google_language_code)

    def get_voice_shortname(self):
        return self.name

    def get_voice_key(self):
        return {
            'name': self.name,
            'language_code': self.google_language_code,
            'ssml_gender': self.google_ssml_gender.name
        }

    def get_options(self):
        return {
            'speaking_rate': {
                'type': 'number',
                'min': 0.25,
                'max': 4.0,
                'default': 1.0
            },
            'pitch': {
                'type': 'number',
                'min': -20.0,
                'max': 20.0,
                'default': 0.0
            },
            cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER: {
                'type': cloudlanguagetools.options.ParameterType.list.name,
                'values': [
                    cloudlanguagetools.options.AudioFormat.mp3.name,
                    cloudlanguagetools.options.AudioFormat.ogg_opus.name,
                ],
                'default': cloudlanguagetools.options.AudioFormat.mp3.name
            }            
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
        'sr': 'sr_cyrl',
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
    return cloudlanguagetools.languages.Language[language_id]

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

    def configure(self, config):
        data_bytes = base64.b64decode(config['key'])
        data_str = data_bytes.decode('utf-8')    
        # write to file
        # note: temp file needs to be a member so it doesn't get collected
        self.google_key_temp_file = tempfile.NamedTemporaryFile()  
        google_key_filename = self.google_key_temp_file.name
        with open(google_key_filename, 'w') as f:
            f.write(data_str)    
            f.close()
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = google_key_filename

    def get_client(self):
        client = google.cloud.texttospeech.TextToSpeechClient()
        return client

    def get_translation_client(self):
        translate_client = google.cloud.translate_v2.Client()
        return translate_client

    def get_tts_audio(self, text, voice_key, options):
        audio_format_str = options.get(cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER, cloudlanguagetools.options.AudioFormat.mp3.name)
        audio_format = cloudlanguagetools.options.AudioFormat[audio_format_str]

        audio_format_map = {
            cloudlanguagetools.options.AudioFormat.mp3: google.cloud.texttospeech.AudioEncoding.MP3,
            cloudlanguagetools.options.AudioFormat.ogg_opus: google.cloud.texttospeech.AudioEncoding.OGG_OPUS
        }

        client = self.get_client()

        ssml_text = '<speak>' + text + '</speak>'
        input_text = google.cloud.texttospeech.SynthesisInput(ssml=ssml_text)

        # Note: the voice can also be specified by name.
        # Names of voices can be retrieved with client.list_voices().
        voice = google.cloud.texttospeech.VoiceSelectionParams(
            name=voice_key['name'],
            language_code=voice_key['language_code'],
            ssml_gender=google.cloud.texttospeech.SsmlVoiceGender[voice_key['ssml_gender']]
        )

        audio_config = google.cloud.texttospeech.AudioConfig(
            audio_encoding=audio_format_map[audio_format],
            speaking_rate=options.get('speaking_rate', 1.0),
            pitch=options.get('pitch', 0.0)
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
            try:
                result.append(GoogleVoice(voice))
            except KeyError:
                logging.error(f'could not process voice for {voice}', exc_info=True)

        return result

    def get_translation_language_list(self):
        data = self.get_translation_languages()
        result_dict = {}
        for entry in data:
            try:
                translation_language = GoogleTranslationLanguage(entry['language'])
                result_dict[translation_language.get_language_code()] = translation_language
            except KeyError:
                logging.error(f'could not process translation language for {entry}', exc_info=True)                
        return result_dict.values()

    def get_transliteration_language_list(self):
        return []

    def get_translation(self, text, from_language_key, to_language_key):
        try:
            client = self.get_translation_client()
            result = client.translate(text, source_language=from_language_key, target_language=to_language_key)
            return html.unescape(result["translatedText"])
        except google.api_core.exceptions.BadRequest as error:
            raise cloudlanguagetools.errors.RequestError(str(error))

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