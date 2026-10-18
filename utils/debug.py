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


def elevenlabs_models():
    """Dump the raw ElevenLabs /v1/models response (model_id, name, tts capability)."""
    import requests
    manager = get_manager()
    service = manager.services[cloudlanguagetools.constants.Service.ElevenLabs.name]
    response = requests.get('https://api.elevenlabs.io/v1/models', headers=service.get_headers(), timeout=30)
    response.raise_for_status()
    for model in response.json():
        print(model['model_id'], '|', model['name'], '| tts:', model['can_do_text_to_speech'], '| languages:', len(model.get('languages', [])))
        pprint.pprint({k: v for k, v in model.items() if k != 'languages'})
        print()


def elevenlabs_unmapped_languages():
    """For each ElevenLabs TTS model, print the language ids that get_audio_language cannot map."""
    import requests
    manager = get_manager()
    service = manager.services[cloudlanguagetools.constants.Service.ElevenLabs.name]
    response = requests.get('https://api.elevenlabs.io/v1/models', headers=service.get_headers(), timeout=30)
    response.raise_for_status()
    for model in response.json():
        if not model['can_do_text_to_speech']:
            continue
        failed = []
        for language_record in model['languages']:
            language_id = language_record['language_id']
            try:
                service.get_audio_language(language_id)
            except Exception as e:
                failed.append(f"{language_id} ({language_record.get('name')}): {type(e).__name__} {e}")
        print(f"{model['model_id']}: {len(model['languages'])} languages, {len(failed)} unmapped")
        for f in failed:
            print('   ', f)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s')
    function_name = sys.argv[1]
    globals()[function_name](*sys.argv[2:])
