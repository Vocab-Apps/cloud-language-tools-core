import os
import epitran as epitran_module

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.transliterationlanguage


class EpitranTransliterationLanguage(cloudlanguagetools.transliterationlanguage.TransliterationLanguage):
    def __init__(self, language, epitran_language_code):
        self.service = cloudlanguagetools.constants.Service.Epitran
        self.language = language
        self.epitran_language_code = epitran_language_code

    def get_transliteration_name(self):
        result = f'{self.language.lang_name} (IPA Pronunciation), {self.service.name} ({self.epitran_language_code})'
        return result

    def get_transliteration_shortname(self):
        result = f'IPA Pronunciation, {self.service.name} ({self.epitran_language_code})'
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
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.am, 'amh-Ethi'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.ar, 'ara-Arab'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.az, 'aze-Cyrl'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.az, 'aze-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.ca, 'cat-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.ceb, 'ceb-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.de, 'deu-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.de, 'deu-Latn-np'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.de, 'deu-Latn-nar'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.en, 'eng-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.fr, 'fra-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.fr, 'fra-Latn-np'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.ha, 'hau-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.hi, 'hin-Deva'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.hu, 'hun-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.id_, 'ind-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.it, 'ita-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.jw, 'jav-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.kk, 'kaz-Cyrl'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.kk, 'kaz-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.rw, 'kin-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.ky, 'kir-Arab'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.ky, 'kir-Cyrl'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.ky, 'kir-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.lo, 'lao-Laoo'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.mr, 'mar-Deva'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.mt, 'mlt-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.ms, 'msa-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.nl, 'nld-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.ny, 'nya-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.pa, 'pan-Guru'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.pl, 'pol-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.ro, 'ron-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.ru, 'rus-Cyrl'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.sn, 'sna-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.so, 'som-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.es, 'spa-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.sw, 'swa-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.sv, 'swe-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.ta, 'tam-Taml'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.te, 'tel-Telu'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.tg, 'tgk-Cyrl'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.th, 'tha-Thai'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.ti, 'tir-Ethi'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.tk, 'tuk-Cyrl'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.tk, 'tuk-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.tr, 'tur-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.uk, 'ukr-Cyrl'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.ug, 'uig-Arab'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.uz, 'uzb-Cyrl'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.uz, 'uzb-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.vi, 'vie-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.xh, 'xho-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.yo, 'yor-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.languages.Language.zu, 'zul-Latn'),            

        ]
        return result

    def get_transliteration(self, text, transliteration_key):
        epi = epitran_module.Epitran(transliteration_key['language_code'])
        result = epi.transliterate(text)
        return result
