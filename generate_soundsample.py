import os
import sys
import json
import tempfile
import shutil 
import logging
import boto3
import pandas
import urllib.parse
import cloudlanguagetools
import cloudlanguagetools.constants
import cloudlanguagetools.servicemanager


def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure()    
    return manager

def generate_audio_language_list():
    records = []
    for audio_language in cloudlanguagetools.constants.AudioLanguage:
        records.append({
            'id': audio_language.name,
            'name': audio_language.audio_lang_name
        })
    data_df = pandas.DataFrame(records)
    filename = 'temp_data_files/audio_languages.csv'
    data_df.to_csv(filename)
    logging.info(f'wrote {filename}')

def generate_sound_sample():
    session = boto3.session.Session()
    client = session.client('s3',
                            region_name=os.environ['SPACE_REGION'],
                            endpoint_url=os.environ['SPACE_ENDPOINT_URL'],
                            aws_access_key_id=os.environ['SPACE_KEY'],
                            aws_secret_access_key=os.environ['SPACE_SECRET'])

    manager = get_manager()
    voice_list = manager.get_tts_voice_list()
    translation_language_list = manager.get_translation_language_list()
    source_text = 'How many languages can you speak ? The more the better !'
    source_language = cloudlanguagetools.constants.Language.en
    source_translation_option = [x for x in translation_language_list if x.language == source_language][0]
    translation_service = 'Azure'
    translations = {}

    entries = []

    for voice in voice_list:
        try:
            audio_language = voice.audio_language
            target_language = audio_language.lang

            dir_path = f'sound_samples/{target_language.lang_name}'
            file_name = f'{voice.get_voice_description()}.mp3'
            final_path = os.path.join(dir_path, file_name)

            if not os.path.isfile(final_path):
                logging.info(f'{final_path} not present, requesting')
                # print(f'source_language: {source_language} target_language: {target_language}')
                if target_language == source_language:
                    # don't translate
                    translation = source_text
                elif target_language not in translations:
                    logging.info(f'need to translate into {target_language}')
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
                logging.info(f'translation into {target_language}: {translation}')
                # print(voice)

                # generate audio
                audio_temp_file = manager.get_tts_audio(translation, voice.service.name, voice.get_voice_key(), {})

                os.makedirs(dir_path, exist_ok=True)

                shutil.copyfile(audio_temp_file.name, final_path)
                logging.info(f'copied into {final_path}')

            # upload to the space
            s3_path = f'{target_language.lang_name}/{voice.get_voice_description()}.mp3'
            client.upload_file(final_path, 'cloud-language-tools-samples', s3_path, ExtraArgs={'ACL':'public-read'})
            # urllib.parse.urlencode(f)
            public_url = f'https://sound-samples.anki.study/{urllib.parse.quote(s3_path)}'

            voice_entry = {
                'audio_language': audio_language.name,
                'language': audio_language.lang.name,
                'language_name': audio_language.lang.lang_name,
                'audio_language_name': audio_language.audio_lang_name,
                'voice_description': voice.get_voice_description(),
                'public_url': public_url
            }

            print(voice_entry)
            entries.append(voice_entry)
        
        except:
            e = sys.exc_info()[0]
            logging.exception(e)

    # write out voice entries as CSV
    voices_df = pandas.DataFrame(entries)
    voices_df.to_csv(f'temp_data_files/voicelist.csv')



if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                        datefmt='%Y%m%d-%H:%M:%S',
                        level=logging.INFO)    
    # generate_sound_sample()
    generate_audio_language_list()