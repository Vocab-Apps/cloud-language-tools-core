import os
import base64
import tempfile
import shutil 
import cloudlanguagetools
import cloudlanguagetools.servicemanager

def test_azure_audio():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure()    

    service = 'Azure'
    voice_id = 'Microsoft Server Speech Text to Speech Voice (en-US, AriaNeural)'
    text = 'hello world'

    result = manager.get_tts_audio(text, service, voice_id, {})
    permanent_file_name = 'azure_output.mp3'
    shutil.copyfile(result, permanent_file_name)
    print(f'tts result: {permanent_file_name}')


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
    test_azure_audio()