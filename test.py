import os
import cloudlanguagetools
import cloudlanguagetools.servicemanager

def main():
    # cloudlanguagetools.text_to_speech('hello world')
    # cloudlanguagetools.list_voices()
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure_azure(os.environ['AZURE_REGION'], os.environ['AZURE_KEY'])
    tts_voice_list = manager.get_tts_voice_list()
    print(tts_voice_list)

if __name__ == '__main__':
    main()