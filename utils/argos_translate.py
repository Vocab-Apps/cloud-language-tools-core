import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
import argostranslate
import argostranslate.translate
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Argos Translate utils')
    parser.add_argument('--action', choices=['install_all_packages', 'test_translation'], required=True)

    args = parser.parse_args()

    if args.action == 'install_all_packages':
        cloudlanguagetools.argostranslate.install_all_packages()
    elif args.action == 'test_translation':
        test_translation()