import sys
import os
import inspect
from typing import List
import pprint
import databind.json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cloudlanguagetools
import cloudlanguagetools.servicemanager
import cloudlanguagetools.ttsvoice

def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure_default()
    return manager

def process_voice(voice):
    return databind.json.dump(voice, cloudlanguagetools.ttsvoice.TtsVoice_v3)

def get_voice_list_hypertts():
    # for hypertts
    manager = get_manager()
    tts_voice_list:  List[cloudlanguagetools.ttsvoice.TtsVoice_v3] = manager.get_tts_voice_list_v3()
    # sort by voice_description
    tts_voice_list.sort(key=lambda voice: (voice.service, voice.name))
    tts_voice_list = [process_voice(voice) for voice in tts_voice_list]
    output_filename = 'temp_data_files/hypertts_voicelist.py'
    with open(output_filename, 'w', encoding='utf8') as f:
        list_formatted = pprint.pformat(tts_voice_list, width=250)
        f.write('VOICE_LIST = ')
        f.write(list_formatted)
        f.close()
    print(f'wrote {output_filename}')    


if __name__ == '__main__':
    get_voice_list_hypertts()