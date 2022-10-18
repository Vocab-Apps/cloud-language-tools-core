import json
import logging

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.options
import cloudlanguagetools.languages
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.translationlanguage
import cloudlanguagetools.transliterationlanguage
import cloudlanguagetools.dictionarylookup
import cloudlanguagetools.errors


logger = logging.getLogger(__name__)


class TestServiceAVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, audio_language, voice_name, voice_id):
        self.audio_language = audio_language
        self.gender = cloudlanguagetools.constants.Gender.Female
        self.voice_name = voice_name
        self.voice_id = voice_id
        self.service = cloudlanguagetools.constants.Service.TestServiceA
        self.service_fee = cloudlanguagetools.constants.ServiceFee.free

    def get_voice_key(self):
        return {
            'voice_id': self.voice_id
        }

    def get_voice_shortname(self):
        return self.voice_name

    def get_options(self):
        return {}

class TestServiceATranslationLanguage(cloudlanguagetools.translationlanguage.TranslationLanguage):
    def __init__(self, language, language_id):
        self.service = cloudlanguagetools.constants.Service.TestServiceA
        self.service_fee = cloudlanguagetools.constants.ServiceFee.free
        self.language = language
        self.language_id = language_id

    def get_language_id(self):
        return self.language_id

class TestServiceATransliterationLanguage(cloudlanguagetools.transliterationlanguage.TransliterationLanguage):
    def __init__(self, language, name, transliteration_key):
        self.service = cloudlanguagetools.constants.Service.TestServiceA
        self.service_fee = cloudlanguagetools.constants.ServiceFee.free
        self.language = language
        self.transliteration_key = transliteration_key
        self.transliteration_name = name

    def get_transliteration_name(self):
        return self.transliteration_name

    def get_transliteration_shortname(self):
        return self.transliteration_name

    def get_transliteration_key(self):
        return self.transliteration_key

class TestServiceADictionaryLookup(cloudlanguagetools.dictionarylookup.DictionaryLookup):
    def __init__(self, language, name, lookup_key):
        self.service = cloudlanguagetools.constants.Service.TestServiceA
        self.service_fee = cloudlanguagetools.constants.ServiceFee.free
        self.language = language
        self.name = name
        self.lookup_key = lookup_key

    def get_lookup_key(self):
        return self.lookup_key

    def get_lookup_name(self):
        return self.name

    def get_lookup_shortname(self):
        return self.name

class TestServiceA(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def configure(self, config):
        pass

    def get_tts_audio(self, text, voice_key, options):
        data_str = json.dumps(
            {
                'type': 'audio',
                'text': text,
                'voice_key': voice_key,
                'options': options
            }
        )

        output_temp_file = tempfile.NamedTemporaryFile()
        output_temp_filename = output_temp_file.name

        f = open(output_temp_filename, 'w')
        f.write(data_str)
        f.close()

        return output_temp_file

    def get_tts_voice_list(self):
        result = []
        result.append(TestServiceAVoice(cloudlanguagetools.languages.AudioLanguage.fr_FR, 'Paul', 'paul'))
        return result

    def get_translation(self, text, from_language_key, to_language_key):
        return json.dumps({
            'text': text,
            'from_language_key': from_language_key,
            'to_language_key': to_language_key
        })
        
    def get_transliteration(self, text, transliteration_key):
        return json.dumps(
            {
                'text': text,
                'transliteration_key': transliteration_key
            }
        )

    def get_translation_language_list(self):
        result = []
        result.append(TestServiceATranslationLanguage(cloudlanguagetools.languages.Language.fr, 'fr'))
        result.append(TestServiceATranslationLanguage(cloudlanguagetools.languages.Language.en, 'en'))
        result.append(TestServiceATranslationLanguage(cloudlanguagetools.languages.Language.zh_cn, 'zh'))
        return result

    def get_transliteration_language_list(self):
        result = []
        result.append(TestServiceATransliterationLanguage(cloudlanguagetools.languages.Language.zh_cn, 'Pinyin', 'pinyin'))
        return result


    def get_dictionary_lookup_list(self):
        result = []
        result.append(TestServiceADictionaryLookup(cloudlanguagetools.languages.Language.fr, 'French', 'french'))
        return result


    def get_dictionary_lookup(self, text, lookup_key):
        return f'dictionary: {text}'





    