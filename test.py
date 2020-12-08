import os
import base64
import json
import tempfile
import shutil 
import cloudlanguagetools
import cloudlanguagetools.servicemanager

def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure()    
    return manager    

def test_azure_audio():
    manager = get_manager()

    service = 'Azure'
    text = 'hello world 2'
    voice_key = {
        'name': 'Microsoft Server Speech Text to Speech Voice (en-US, AriaNeural)' 
    }

    result = manager.get_tts_audio(text, service, voice_key, {})
    permanent_file_name = 'azure_output.mp3'
    shutil.copyfile(result.name, permanent_file_name)
    print(f'tts result: {permanent_file_name}')

def test_google_audio():
    manager = get_manager()

    service = 'Google'
    text = 'hello world test 1'

    voice_key = {
        'language_code': "en-US",
        'name': "en-US-Standard-C",
        'ssml_gender': "FEMALE"
    }    

    result = manager.get_tts_audio(text, service, voice_key, {})
    permanent_file_name = 'google_output.mp3'
    shutil.copyfile(result.name, permanent_file_name)
    print(f'tts result: {permanent_file_name}')


def get_voice_list():
    manager = get_manager()
    tts_voice_list_json = manager.get_tts_voice_list_json()
    print(tts_voice_list_json)    
    output_filename = 'voicelist.json'
    with open(output_filename, 'w') as f:
        f.write(json.dumps(tts_voice_list_json, indent=4, sort_keys=True))
        f.close()
    print(f'wrote {output_filename}')

def get_translation_language_list():
    manager = get_manager()
    language_list_json = manager.get_translation_language_list_json()
    #print(tts_voice_list_json)    
    output_filename = 'temp_data_files/translation_language_list.json'
    with open(output_filename, 'w') as f:
        f.write(json.dumps(language_list_json, indent=4, sort_keys=True))
        f.close()
    print(f'wrote {output_filename}')


def get_azure_translation_languages():
    manager = get_manager()
    data = manager.services[cloudlanguagetools.constants.Service.Azure.name].get_translation_languages()
    # print(data)
    output_filename = 'azure_translation_languages.json'
    with open(output_filename, 'w') as f:
        f.write(json.dumps(data, sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': ')))
        f.close()
    print(f'wrote output to {output_filename}')


def get_google_translation_languages():
    manager = get_manager()
    data = manager.services[cloudlanguagetools.constants.Service.Google.name].get_translation_languages()
    # print(data)
    output_filename = 'google_translation_languages.json'
    with open(output_filename, 'w') as f:
        f.write(json.dumps(data, sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': ')))
        f.close()
    print(f'wrote output to {output_filename}')    

def output_languages_enum():
    manager = get_manager()
    data_google = manager.services[cloudlanguagetools.constants.Service.Google.name].get_translation_languages()
    data_azure = manager.services[cloudlanguagetools.constants.Service.Azure.name].get_translation_languages()

    language_map = {}

    for entry in data_google:
        language_map[entry['language']] = entry['name']

    for key, data in data_azure['translation'].items():
        language_map[key] = data['name']

    output_filename = 'languages_enum.txt'
    with open(output_filename, 'w') as f:
        for key, name in language_map.items():
            output = f"{key} = (\"{name}\")\n"
            f.write(output)
        f.close()
    print(f'wrote output to {output_filename}')    



if __name__ == '__main__':
    # test_azure_audio()
    # test_google_audio()
    #get_voice_list()
    # get_azure_translation_languages()
    # get_google_translation_languages()
    #output_languages_enum()
    get_translation_language_list()