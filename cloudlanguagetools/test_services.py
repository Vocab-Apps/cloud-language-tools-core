import json
import logging
import tempfile

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


class TestServiceVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, audio_language, voice_name, voice_id, service, service_fee):
        self.audio_language = audio_language
        self.gender = cloudlanguagetools.constants.Gender.Female
        self.voice_name = voice_name
        self.voice_id = voice_id
        self.service = service
        self.service_fee = service_fee

    def get_voice_key(self):
        return {
            'voice_id': self.voice_id
        }

    def get_voice_shortname(self):
        return self.voice_name

    def get_options(self):
        return {}

class TestServiceTranslationLanguage(cloudlanguagetools.translationlanguage.TranslationLanguage):
    def __init__(self, language, language_id, service, service_fee):
        self.service = service
        self.service_fee = service_fee
        self.language = language
        self.language_id = language_id

    def get_language_id(self):
        return self.language_id

class TestServiceTransliterationLanguage(cloudlanguagetools.transliterationlanguage.TransliterationLanguage):
    def __init__(self, language, name, transliteration_key, service, service_fee):
        self.service = service
        self.service_fee = service_fee
        self.language = language
        self.transliteration_key = transliteration_key
        self.transliteration_name = name

    def get_transliteration_name(self):
        return self.transliteration_name

    def get_transliteration_shortname(self):
        return self.transliteration_name

    def get_transliteration_key(self):
        return self.transliteration_key

class TestServiceDictionaryLookup(cloudlanguagetools.dictionarylookup.DictionaryLookup):
    def __init__(self, language, name, lookup_key, service, service_fee):
        self.service = service
        self.service_fee = service_fee
        self.language = language
        self.name = name
        self.lookup_key = lookup_key

    def get_lookup_key(self):
        return self.lookup_key

    def get_lookup_name(self):
        return self.name

    def get_lookup_shortname(self):
        return self.name

class TestServiceBase(cloudlanguagetools.service.Service):
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
        result.append(TestServiceVoice(cloudlanguagetools.languages.AudioLanguage.fr_FR, 'Paul', 'paul', 
            self.SERVICE, self.SERVICE_FEE))
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
        result.append(TestServiceTranslationLanguage(cloudlanguagetools.languages.Language.fr, 'fr', self.SERVICE, self.SERVICE_FEE))
        result.append(TestServiceTranslationLanguage(cloudlanguagetools.languages.Language.en, 'en', self.SERVICE, self.SERVICE_FEE))
        result.append(TestServiceTranslationLanguage(cloudlanguagetools.languages.Language.zh_cn, 'zh', self.SERVICE, self.SERVICE_FEE))
        return result

    def get_transliteration_language_list(self):
        result = []
        result.append(TestServiceTransliterationLanguage(cloudlanguagetools.languages.Language.zh_cn, 'Pinyin', 'pinyin', self.SERVICE, self.SERVICE_FEE))
        return result


    def get_dictionary_lookup_list(self):
        result = []
        result.append(TestServiceDictionaryLookup(cloudlanguagetools.languages.Language.fr, 'French', 'french', self.SERVICE, self.SERVICE_FEE))
        result.append(TestServiceDictionaryLookup(cloudlanguagetools.languages.Language.zh_cn, 'Chinese', 'zh', self.SERVICE, self.SERVICE_FEE))
        return result


    def get_dictionary_lookup(self, text, lookup_key):
        return json.dumps({
            'type': 'dictionary',
            'text': text,
            'lookup_key': lookup_key
        })


class TestServiceA(TestServiceBase):
    SERVICE = cloudlanguagetools.constants.Service.TestServiceA
    SERVICE_FEE = cloudlanguagetools.constants.ServiceFee.free

class TestServiceB(TestServiceBase):
    SERVICE = cloudlanguagetools.constants.Service.TestServiceB
    SERVICE_FEE = cloudlanguagetools.constants.ServiceFee.paid


    