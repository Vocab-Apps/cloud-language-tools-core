import os
import base64
import json
import tempfile
import shutil 
import unittest
import pydub
import pydub.playback
import cloudlanguagetools
import cloudlanguagetools.constants
import cloudlanguagetools.servicemanager


def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure()    
    return manager

def generate_sound_sample():
    manager = get_manager()
    voice_list = manager.get_tts_voice_list()
    translation_language_list = manager.get_translation_language_list()
    source_text = 'How many languages can you speak ? The more the better !'
    source_language = cloudlanguagetools.constants.Language.en
    source_translation_option = [x for x in translation_language_list if x.language == source_language][0]
    translation_service = 'Azure'
    translations = {}
    for voice in voice_list:
        audio_language = voice.audio_language
        target_language = audio_language.lang
        print(f'source_language: {source_language} target_language: {target_language}')
        if target_language == source_language:
            # don't translate
            translation = source_text
        elif target_language not in translations:
            print(f'need to translate into {target_language}')
            # translate
            # get azure translation service
            target_translation_option = [x for x in translation_language_list if x.language == target_language][0]
            # print(source_translation_option.json_obj())
            # print(target_translation_option.json_obj())
            translation = manager.get_translation(source_text, translation_service, source_translation_option.get_language_id(), target_translation_option.get_language_id())
            translations[target_language] = translation
            # print(translation)
        else:
            translation = translations[target_language]
        print(f'translation into {target_language}: {translation}')
        print(voice)



if __name__ == '__main__':
    generate_sound_sample()