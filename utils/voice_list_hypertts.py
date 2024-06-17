import sys
import os
import logging
from typing import List
import pprint
import json
import databind.json

logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                    datefmt='%Y%m%d-%H:%M:%S',
                    stream=sys.stdout,
                    level=logging.INFO)

logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cloudlanguagetools
import cloudlanguagetools.servicemanager
import cloudlanguagetools.ttsvoice

def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure_default()
    return manager

def process_voice(voice: cloudlanguagetools.ttsvoice.TtsVoice_v3):
    logger.info(f'processing voice {voice}')
    return f"""
        voice.TtsVoice_v3(
            name='{voice.name}',
            voice_key={voice.voice_key},
            options={voice.options},
            service='{voice.service.name}',
            gender=constants.Gender.{voice.gender.name},
            audio_languages=[
                {', '.join([f'languages.AudioLanguage.{audio_lang.name}' for audio_lang in voice.audio_languages])}
            ],
            service_fee=constants.ServiceFee.{voice.service_fee.name}
        )
"""

def get_voice_list_hypertts():
    # for hypertts
    manager = get_manager()
    tts_voice_list:  List[cloudlanguagetools.ttsvoice.TtsVoice_v3] = manager.get_tts_voice_list_v3()
    # sort by voice_description
    tts_voice_list.sort(key=lambda voice: (voice.service, voice.name))
    voice_list_str_array = [process_voice(voice) for voice in tts_voice_list]
    output_filename = 'temp_data_files/hypertts_voicelist.py'
    
    with open(output_filename, 'w', encoding='utf8') as f:
        f.write("""
import sys

constants = __import__('constants', globals(), locals(), [], sys._addon_import_level_services)
languages = __import__('languages', globals(), locals(), [], sys._addon_import_level_services)
voice = __import__('voice', globals(), locals(), [], sys._addon_import_level_services)                

VOICE_LIST = [
        """)
        f.write(', \n'.join(voice_list_str_array))
        f.write("""]""")

    print(f'wrote {output_filename}')    


if __name__ == '__main__':
    # setup basic logging at info level
    logger.info('starting to generate hypertts voice list')
    get_voice_list_hypertts()