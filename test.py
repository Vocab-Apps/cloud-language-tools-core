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
    voice_id = 'Microsoft Server Speech Text to Speech Voice (en-US, AriaNeural)'
    text = 'hello world'

    result = manager.get_tts_audio(text, service, voice_id, {})
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




def main():
    # cloudlanguagetools.text_to_speech('hello world')
    # cloudlanguagetools.list_voices()
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure()


    # tts_voice_list = manager.get_tts_voice_list()
    # print(tts_voice_list)
    #tts_voice_list_json = manager.get_tts_voice_list_json()
    #print(tts_voice_list_json)
    


if __name__ == '__main__':
    # test_azure_audio()
    test_google_audio()
    #get_voice_list()