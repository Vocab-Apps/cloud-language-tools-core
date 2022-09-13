import cloudlanguagetools.service
import cloudlanguagetools.translationlanguage

import logging
# configure argos package location before importing argos
import clt_argostranslate
clt_argostranslate.configure_package_dir()
import argostranslate
import argostranslate.package
import argostranslate.translate

logger = logging.getLogger(__name__)


# map from the argos translate codes to our internal language codes
def get_translation_language_enum(language_id):
    # print(f'language_id: {language_id}')
    argos_language_id_override_map = {
        'zh': 'zh_cn',
        'id': 'id_',
        'pt': 'pt_pt'
    }
    if language_id in argos_language_id_override_map:
        language_id = argos_language_id_override_map[language_id]
    return cloudlanguagetools.languages.Language[language_id]

class ArgosTranslationLanguage(cloudlanguagetools.translationlanguage.TranslationLanguage):
    def __init__(self, language_id):
        self.service = cloudlanguagetools.constants.Service.ArgosTranslate
        self.language_id = language_id
        self.language = get_translation_language_enum(language_id)

    def get_language_id(self):
        return self.language_id

# NOTE: this service is disabled
class ArgosTranslateService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def configure(self, config):
        pass

    def get_tts_audio(self, text, voice_key, options):
        raise Exception('not supported')

    def get_tts_voice_list(self):
        return []

    def get_translation(self, text, from_language_key, to_language_key):

        installed_languages = argostranslate.translate.get_installed_languages()
        from_lang = list(filter(
            lambda x: x.code == from_language_key,
            installed_languages))[0]
        to_lang = list(filter(
            lambda x: x.code == to_language_key,
            installed_languages))[0]
        translation = from_lang.get_translation(to_lang)
        translated_text = translation.translate(text)

        return translated_text

    def get_transliteration(self, text, transliteration_key):
        raise Exception('not supported')

    def get_translation_language_list(self):
        result = []
        installed_languages = argostranslate.translate.get_installed_languages()
        for language in installed_languages:
            try:
                result.append(ArgosTranslationLanguage(language.code))
            except KeyError:
                logger.error(f'could not process translation language for {language}, {language.code}', exc_info=True)

        return result

    def get_transliteration_language_list(self):
        return []
