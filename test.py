import os
import base64
import tempfile
import cloudlanguagetools
import cloudlanguagetools.servicemanager

def main():
    # cloudlanguagetools.text_to_speech('hello world')
    # cloudlanguagetools.list_voices()
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure_azure(os.environ['AZURE_REGION'], os.environ['AZURE_KEY'])

    # extract google key
    google_key = os.environ['GOOGLE_KEY']
    data_bytes = base64.b64decode(google_key)
    data_str = data_bytes.decode('utf-8')    
    # write to file
    temp_file = tempfile.NamedTemporaryFile()  
    google_key_filename = temp_file.name    
    with open(google_key_filename, 'w') as f:
        f.write(data_str)    
        f.close()
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = google_key_filename

    # tts_voice_list = manager.get_tts_voice_list()
    # print(tts_voice_list)
    tts_voice_list_json = manager.get_tts_voice_list_json()
    print(tts_voice_list_json)


if __name__ == '__main__':
    main()