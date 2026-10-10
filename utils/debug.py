import os
import sys
import logging
import pprint
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import cloudlanguagetools.servicemanager
import cloudlanguagetools.constants

# temporary debugging helpers, run with: uv run python utils/debug.py <function name>


def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure_default()
    return manager


def gemini_3_8_sample(text='This is the best restaurant in town.', voice_name='Kore',
        model='gemini-3.8-flash-tts', audio_format='mp3', prompt='', output_filename='gemini_3_8_sample'):
    """Synthesize one sample with a Gemini 3.8 model and copy it next to the current directory."""
    manager = get_manager()
    options = {'model': model, 'format': audio_format}
    if prompt:
        options['prompt'] = prompt
    audio_temp_file = manager.get_tts_audio(text, cloudlanguagetools.constants.Service.Gemini.name, {'name': voice_name}, options)
    extension = {'ogg_opus': 'ogg', 'mp3_hq': 'mp3'}.get(audio_format, audio_format)
    output_path = f'{output_filename}.{extension}'
    shutil.copy(audio_temp_file.name, output_path)
    print(f'wrote {output_path}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s')
    function_name = sys.argv[1]
    globals()[function_name](*sys.argv[2:])
