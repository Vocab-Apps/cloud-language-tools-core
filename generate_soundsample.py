import os
import json
import tempfile
import shutil 
import logging
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
        # print(voice)

        # generate audio
        audio_temp_file = manager.get_tts_audio(translation, voice.service.name, voice.get_voice_key(), {})

        dir_path = f'sound_samples/{target_language.lang_name}'
        file_name = f'{voice.get_voice_description()}.mp3'
        os.makedirs(dir_path)
        final_path = os.path.join(dir_path, file_name)
        shutil.copyfile(audio_temp_file.name, final_path)
        logging.info(f'copied into {final_path}')



if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                        datefmt='%Y%m%d-%H:%M:%S',
                        level=logging.INFO)    
    generate_sound_sample()