import os
import epitran as epitran_module

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.transliterationlanguage


class EpitranTransliterationLanguage(cloudlanguagetools.transliterationlanguage.TransliterationLanguage):
    def __init__(self, language, epitran_language_code):
        self.service = cloudlanguagetools.constants.Service.Epitran
        self.language = language
        self.epitran_language_code = epitran_language_code

    def get_transliteration_name(self):
        result = f'{self.language.lang_name} (IPA Pronunciation), {self.service.name} ({self.epitran_language_code})'
        return result

    def get_transliteration_key(self):
        key = {
            'language_code': self.epitran_language_code
        }
        return key

class EpitranService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def get_tts_voice_list(self):
        return []

    def get_translation_language_list(self):
        return []

    def get_transliteration_language_list(self):
        result = [
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.fr, 'fra-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.fr, 'fra-Latn-np'),
        ]
        return result

    def get_transliteration(self, text, transliteration_key):
        epi = epitran_module.Epitran(transliteration_key['language_code'])
        result = epi.transliterate(text)
        return result
