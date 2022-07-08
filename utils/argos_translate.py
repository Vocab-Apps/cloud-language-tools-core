import os
import sys
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
import argostranslate
import argostranslate.translate
import cloudlanguagetools.servicemanager
import cloudlanguagetools.argostranslate


def test_translation():
    from_code = 'en'
    to_code = 'fr'

    installed_languages = argostranslate.translate.get_installed_languages()
    from_lang = list(filter(
        lambda x: x.code == from_code,
        installed_languages))[0]
    to_lang = list(filter(
        lambda x: x.code == to_code,
        installed_languages))[0]
    translation = from_lang.get_translation(to_lang)
    translatedText = translation.translate("I am working on my project.")
    print(translatedText)

def list_languages():
    installed_languages = argostranslate.translate.get_installed_languages()
    for language in installed_languages:
        print(language)
        print(type(language))
        print(language.code)

def get_translation_language_list():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    argostranslate_service = manager.services[cloudlanguagetools.constants.Service.ArgosTranslate.name]
    translation_language_list = argostranslate_service.get_translation_language_list()

if __name__ == '__main__':
    logger = logging.getLogger()
    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])    
    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                        datefmt='%Y%m%d-%H:%M:%S',
                        stream=sys.stdout,
                        level=logging.INFO)    

    parser = argparse.ArgumentParser(description='Argos Translate utils')
    parser.add_argument('--action', choices=['install_all_packages', 'test_translation', 'list_languages', 'get_translation_language_list'], required=True)

    args = parser.parse_args()

    if args.action == 'install_all_packages':
        cloudlanguagetools.argostranslate.install_all_packages()
    elif args.action == 'test_translation':
        test_translation()
    elif args.action == 'list_languages':
        list_languages()
    elif args.action == 'get_translation_language_list':
        get_translation_language_list()