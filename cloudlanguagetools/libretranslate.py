import cloudlanguagetools.service
import cloudlanguagetools.translationlanguage
import requests

import logging
import pprint


logger = logging.getLogger(__name__)


# map from the argos translate codes to our internal language codes
def get_translation_language_enum(language_id):
    argos_language_id_override_map = {
        'zh': 'zh_cn',
        'id': 'id_',
        'pt': 'pt_pt'
    }
    if language_id in argos_language_id_override_map:
        language_id = argos_language_id_override_map[language_id]
    return cloudlanguagetools.languages.Language[language_id]

class LibreTranslateLanguage(cloudlanguagetools.translationlanguage.TranslationLanguage):
    def __init__(self, language_id):
        self.service = cloudlanguagetools.constants.Service.LibreTranslate
        self.language_id = language_id
        self.language = get_translation_language_enum(language_id)

    def get_language_id(self):
        return self.language_id


class LibreTranslateService(cloudlanguagetools.service.Service):
    BASE_URL = 'http://libretranslate.vocab.ai'

    def __init__(self):
        pass

    def configure(self, config):
        pass

    def get_tts_audio(self, text, voice_key, options):
        raise Exception('not supported')

    def get_tts_voice_list(self):
        return []

    def get_translation(self, text, from_language_key, to_language_key):
        data = {
            'q': text,
            'source': from_language_key,
            'target': to_language_key
        }
        logger.debug(f'translating using parameters: {data}')
        response = requests.post(self.BASE_URL + '/translate', data=data, timeout=cloudlanguagetools.constants.RequestTimeout)
        response_data = response.json()        

        if response.status_code == 200:
            return response_data['translatedText']

        error_message = f'LibreTranslate: could not translate text [{text}] from {from_language_key} to {to_language_key} ({response_data})'
        raise cloudlanguagetools.errors.RequestError(error_message)

    def get_transliteration(self, text, transliteration_key):
        raise Exception('not supported')

    def get_translation_language_list(self):
        result = []

        response = requests.get(self.BASE_URL + '/languages', timeout=cloudlanguagetools.constants.RequestTimeout)
        language_list = response.json()
        for language in language_list:
            try:
                result.append(LibreTranslateLanguage(language['code']))
            except KeyError:
                logger.error(f'could not process translation language for {language}, {language.code}', exc_info=True)

        return result

    def get_transliteration_language_list(self):
        return []
