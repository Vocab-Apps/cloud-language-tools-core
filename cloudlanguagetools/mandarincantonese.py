import json
import requests
import cloudlanguagetools.constants

class MandarinCantoneseTransliteration(cloudlanguagetools.transliterationlanguage.TransliterationLanguage):
    def __init__(self, language, conversion_type, tone_numbers, spaces):
        self.service = cloudlanguagetools.constants.Service.MandarinCantonese
        self.language = language
        self.conversion_type = conversion_type
        self.tone_numbers = tone_numbers
        self.spaces = spaces

    def get_transliteration_name(self):
        conversion_type_str = self.conversion_type.capitalize()
        tone_numbers_str = "Diacritics"
        if self.tone_numbers:
            tone_numbers_str = "Tone Numbers"
        spaces_str = ""
        if self.spaces:
            spaces_str = "Spaces"
        return f'{self.language.lang_name} to {conversion_type_str} ({tone_numbers_str} {spaces_str}), {self.service.name}'

    def get_transliteration_key(self):
        return {
            'conversion_type': self.conversion_type,
            'tone_numbers': self.tone_numbers,
            'spaces': self.spaces
        }

class MandarinCantoneseService(cloudlanguagetools.service.Service):
    def __init__(self):
        self.base_url = 'https://apiv2.mandarincantonese.com'


    def get_tts_voice_list(self):
        return []

    def get_translation_language_list(self):
        return []

    def get_transliteration_language_list(self):
        result = []
        for tone_numbers in [True, False]:
            for spaces in [True, False]:
                result.append(MandarinCantoneseTransliteration(cloudlanguagetools.constants.Language.zh_cn, 'pinyin', tone_numbers, spaces))
                result.append(MandarinCantoneseTransliteration(cloudlanguagetools.constants.Language.zh_tw, 'pinyin', tone_numbers, spaces))
                result.append(MandarinCantoneseTransliteration(cloudlanguagetools.constants.Language.yue, 'jyutping', tone_numbers, spaces))
        return result

    def get_transliteration(self, text, transliteration_key):
        response = requests.post(self.base_url + '/convert', json={
            'text': text,
            'conversion_type': transliteration_key['conversion_type'],
            'tone_numbers': transliteration_key['tone_numbers'],
            'spaces': transliteration_key['spaces']
        }, timeout=cloudlanguagetools.constants.RequestTimeout)
        data = json.loads(response.content)
        return data['romanization']