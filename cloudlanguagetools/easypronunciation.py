import os
import requests
import urllib.parse

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.transliterationlanguage

VARIANT_JAPANESE_ROMAJI = 'Romaji'
VARIANT_JAPANESE_KANA = 'Kana'

class EasyPronunciationTransliterationLanguage(cloudlanguagetools.transliterationlanguage.TransliterationLanguage):
    def __init__(self, url_path, language, api_params, api_key, variant = None):
        self.service = cloudlanguagetools.constants.Service.EasyPronunciation
        self.url_path = url_path
        self.language = language
        self.api_params = api_params
        self.api_key = api_key
        self.variant = variant

    def get_transliteration_name(self):
        result = f'{self.language.lang_name} (IPA Pronunciation), {self.service.name}'
        if self.variant != None:
            result = f'{self.language.lang_name} ({self.variant}), {self.service.name}'
        return result

    def get_transliteration_shortname(self):
        result = f'IPA Pronunciation, {self.service.name}'
        if self.variant != None:
            result = f'{self.variant}, {self.service.name}'
        return result        

    def get_transliteration_key(self):
        key = {
            'url_path': self.url_path,
            'api_params': self.api_params,
            'api_key': self.api_key,
        }
        if self.variant != None:
            key['variant'] = self.variant
        return key

class EasyPronunciationService(cloudlanguagetools.service.Service):
    def __init__(self):
        self.url_base = 'https://easypronunciation.com'

    def configure(self, config):
        self.api_keys = {
            'french': config['french_api_key'],
            'english': config['english_api_key'],
            'italian': config['italian_api_key'],
            'portuguese': config['portuguese_api_key'],
            'japanese': config['japanese_api_key'],
            'spanish': config['spanish_api_key'],
            'german': config['german_api_key'],
            'russian': config['russian_api_key']
        }

    def get_tts_voice_list(self):
        return []

    def get_translation_language_list(self):
        return []

    def get_transliteration_language_list(self):
        result = [
            EasyPronunciationTransliterationLanguage('/french-api.php', cloudlanguagetools.languages.Language.fr,
            {
                'version': 1,
                'use_un_symbol': 1,
                'vowel_lengthening':1,
                'show_rare_pronunciations':0,
                'french_liaison_styling': 'one_by_one',
                'spell_numbers':1
            }, 'french'),

            EasyPronunciationTransliterationLanguage('/english-api.php', cloudlanguagetools.languages.Language.en,
            {
                'version': 1,
                'english_phonetics_algorithm': 'american_miscellaneous_sources',
                'Convert_to_english':'ipa',
                'add_aspiration_symbol': 1,
                'narrow_transcription':1,
                'r_replacement':1,
                'cot_caught_merger':1,
                'er_replacement':1,
                'elongation_symbol_after_i_and_u':'always',
                'only_i_for_es_ed_endings':0,
                'show_rare_pronunciations':1,
                'spell_numbers':1
            }, 'english'),

            EasyPronunciationTransliterationLanguage('/italian-api.php', cloudlanguagetools.languages.Language.it,
            {
                'version':1,
                'spell_numbers':1
            }, 'italian'),

            EasyPronunciationTransliterationLanguage('/japanese-api.php', cloudlanguagetools.languages.Language.ja,
            {
                'version':1,
                'style':'slash',
                'devoicing':1,
                'weakening':1
            }, 'japanese', VARIANT_JAPANESE_ROMAJI),

            EasyPronunciationTransliterationLanguage('/japanese-api.php', cloudlanguagetools.languages.Language.ja,
            {
                'version':1,
                'style':'slash',
                'devoicing':1,
                'weakening':1
            }, 'japanese', VARIANT_JAPANESE_KANA),

            EasyPronunciationTransliterationLanguage('/portuguese-api.php', cloudlanguagetools.languages.Language.pt_pt,
            {
                'version':1,
                'portuguese_dialect':'EP',
                'spell_numbers':1,
            }, 'portuguese'),

            EasyPronunciationTransliterationLanguage('/portuguese-api.php', cloudlanguagetools.languages.Language.pt_br,
            {
                'version':1,
                'portuguese_dialect':'BP',
                'spell_numbers':1,
            }, 'portuguese'),

            EasyPronunciationTransliterationLanguage('/spanish-api.php', cloudlanguagetools.languages.Language.es,
            {
                'version':1,
                'split_into_syllables':0,
                'caza_casa_merger':1,
                'callo_cayo_merger':1,
                'allophones_for_l_m_n':1,
                'x_before_consonants':'s',
                'spell_numbers':1
            }, 'spanish'),

            EasyPronunciationTransliterationLanguage('/german-api.php', cloudlanguagetools.languages.Language.de,
            {
                'version':1,
                'split_into_syllables':1,
                'spell_numbers':1
            }, 'german'),

            EasyPronunciationTransliterationLanguage('/russian-api.php', cloudlanguagetools.languages.Language.ru,
            {
                'version':1,
                'Convert_to_russian':'IPA',
                'do_not_restore_yo': 0,
                'split_into_syllables':1,
                'spell_numbers':1
            }, 'russian'),

        ]
        return result

    def get_transliteration(self, text, transliteration_key):
        api_url = self.url_base + transliteration_key['url_path']
        parameters = {
            'access_token': self.api_keys[transliteration_key['api_key']],
            'phrase': text
        }
        parameters.update(transliteration_key['api_params'])
        encoded_parameters = urllib.parse.urlencode(parameters)
        full_url = f'{api_url}?{encoded_parameters}'

        # print(full_url)
        request = requests.get(full_url)
        result = request.json()

        # print(request)
        # print(result)

        if 'phonetic_transcription' in result:
            phonetic_transcription = result['phonetic_transcription']
            result_components = []
            for entry in phonetic_transcription:
                result_components.append(entry['transcriptions'][0])

            if 'variant' in transliteration_key:
                if transliteration_key['variant'] == VARIANT_JAPANESE_ROMAJI:
                    result_components = [x['romaji'] for x in result_components]
                if transliteration_key['variant'] == VARIANT_JAPANESE_KANA:
                    result_components = [x['kana'] for x in result_components]

            # print(result_components)
            return ' '.join(result_components)

        # an error occured
        error_message = f'EasyPronunciation: could not perform conversion: {str(result)}'
        raise cloudlanguagetools.errors.RequestError(error_message)
