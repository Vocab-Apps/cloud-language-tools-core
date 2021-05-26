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
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.am, 'amh-Ethi'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.ar, 'ara-Arab'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.az, 'aze-Cyrl'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.az, 'aze-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.ca, 'cat-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.ceb, 'ceb-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.de, 'deu-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.de, 'deu-Latn-np'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.de, 'deu-Latn-nar'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.en, 'eng-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.fr, 'fra-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.fr, 'fra-Latn-np'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.ha, 'hau-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.hi, 'hin-Deva'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.hu, 'hun-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.id_, 'ind-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.it, 'ita-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.jw, 'jav-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.kk, 'kaz-Cyrl'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.kk, 'kaz-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.rw, 'kin-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.ky, 'kir-Arab'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.ky, 'kir-Cyrl'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.ky, 'kir-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.lo, 'lao-Laoo'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.mr, 'mar-Deva'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.mt, 'mlt-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.ms, 'msa-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.nl, 'nld-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.ny, 'nya-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.pa, 'pan-Guru'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.pl, 'pol-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.ro, 'ron-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.ru, 'rus-Cyrl'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.sn, 'sna-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.so, 'som-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.es, 'spa-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.sw, 'swa-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.sv, 'swe-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.ta, 'tam-Taml'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.te, 'tel-Telu'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.tg, 'tgk-Cyrl'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.th, 'tha-Thai'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.ti, 'tir-Ethi'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.tk, 'tuk-Cyrl'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.tk, 'tuk-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.tr, 'tur-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.uk, 'ukr-Cyrl'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.ug, 'uig-Arab'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.uz, 'uzb-Cyrl'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.uz, 'uzb-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.vi, 'vie-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.xh, 'xho-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.yo, 'yor-Latn'),
            EpitranTransliterationLanguage(cloudlanguagetools.constants.Language.zu, 'zul-Latn'),            

        ]
        return result

    def get_transliteration(self, text, transliteration_key):
        epi = epitran_module.Epitran(transliteration_key['language_code'])
        result = epi.transliterate(text)
        return result
