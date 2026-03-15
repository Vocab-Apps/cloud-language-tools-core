import os
import sys
import logging
import pprint
import base64
import json
import tempfile
import shutil
import subprocess
import unittest
import pydub
import pydub.playback
# import epitran
# import pandas
import requests
import re
import secrets
# import redisdb

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import cloudlanguagetools
import cloudlanguagetools.servicemanager
import cloudlanguagetools.languages
import cloudlanguagetools.constants
import cloudlanguagetools.errors


def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure_default()
    return manager


def get_watson_voice_list():
    manager = get_manager()
    #tts_voice_list_json = manager.get_tts_voice_list_json()
    # print(tts_voice_list_json)
    data = manager.services[cloudlanguagetools.constants.Service.Watson.name].list_voices()
    output_filename = 'temp_data_files/watson_voicelist.json'
    with open(output_filename, 'w', encoding='utf8') as f:
        f.write(json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False))
        f.close()
    print(f'wrote {output_filename}')

def get_watson_translation_languages():
    manager = get_manager()
    #tts_voice_list_json = manager.get_tts_voice_list_json()
    # print(tts_voice_list_json)
    data = manager.services[cloudlanguagetools.constants.Service.Watson.name].get_translation_language_list()
    pprint.pprint(data)

def get_google_voice_list():
    manager = get_manager()
    voice_list = manager.services[cloudlanguagetools.constants.Service.Google.name].get_tts_voice_list()

    # Convert voice objects to JSON-serializable format
    voice_list_json = [voice.__dict__ for voice in voice_list]

    output_filename = 'temp_data_files/google_voice_list.json'
    with open(output_filename, 'w', encoding='utf8') as f:
        f.write(json.dumps(voice_list_json, indent=4, sort_keys=True, ensure_ascii=False, default=str))
        f.close()
    print(f'wrote {output_filename}')

    return voice_list

def get_amazon_voice_list():
    manager = get_manager()
    #tts_voice_list_json = manager.get_tts_voice_list_json()
    # print(tts_voice_list_json)
    manager.services[cloudlanguagetools.constants.Service.Amazon.name].get_tts_voice_list()

def get_forvo_voice_list():
    manager = get_manager()
    #tts_voice_list_json = manager.get_tts_voice_list_json()
    # print(tts_voice_list_json)
    voice_list = manager.services[cloudlanguagetools.constants.Service.Forvo.name].get_tts_voice_list_v3()
    pprint.pprint(voice_list)

def get_amazon_voice_list_awesometts():
    manager = get_manager()
    #tts_voice_list_json = manager.get_tts_voice_list_json()
    # print(tts_voice_list_json)
    voice_list = manager.services[cloudlanguagetools.constants.Service.Amazon.name].get_tts_voice_list()
    # print(voice_list)
    for voice in voice_list:
        code = f"AmazonVoice(Language.{voice.audio_language.name}, Gender.{voice.gender.name}, '{voice.name}', '{voice.voice_id}', '{voice.engine}'),"
        print(code)

def get_elevenlabs_voice_list():
    manager = get_manager()
    voice_list = manager.services[cloudlanguagetools.constants.Service.ElevenLabs.name].get_tts_voice_list()
    # pprint.pprint(voice_list)
    # print names of voices in voice_list
    for voice in voice_list:
        print(voice)

def test_elevenlabs_pagination():
    """Test that ElevenLabs API pagination assertions are working"""
    manager = get_manager()
    service = manager.services[cloudlanguagetools.constants.Service.ElevenLabs.name]
    headers = service.get_headers()

    print("=" * 80)
    print("ElevenLabs Pagination Test")
    print("=" * 80)

    # Get raw API response to check pagination fields
    url = "https://api.elevenlabs.io/v1/voices"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    print(f"Response keys: {data.keys()}")

    if 'has_more' in data:
        print(f"has_more: {data['has_more']}")
    else:
        print("has_more: field not present in response")

    if 'total_count' in data:
        print(f"total_count: {data['total_count']}")
    else:
        print("total_count: field not present in response")

    if 'page_size' in data:
        print(f"page_size: {data['page_size']}")
    else:
        print("page_size: field not present in response")

    if 'next_page_start_after' in data:
        print(f"next_page_start_after: {data['next_page_start_after']}")
    else:
        print("next_page_start_after: field not present in response")

    print(f"Number of voices in response: {len(data['voices'])}")

    # Now test that our methods work with assertions
    print("\nTesting get_tts_voice_list() with pagination assertions...")
    try:
        voice_list = service.get_tts_voice_list()
        print(f"✓ get_tts_voice_list() succeeded, returned {len(voice_list)} voices")
    except AssertionError as e:
        print(f"✗ get_tts_voice_list() assertion failed: {e}")

    print("\nTesting get_tts_voice_list_v3() with pagination assertions...")
    try:
        voice_list_v3 = service.get_tts_voice_list_v3()
        print(f"✓ get_tts_voice_list_v3() succeeded, returned {len(voice_list_v3)} voices")
    except AssertionError as e:
        print(f"✗ get_tts_voice_list_v3() assertion failed: {e}")

def test_elevenlabs_voice_filtering():
    """Test that ElevenLabs voice filtering is working correctly after the fix"""
    manager = get_manager()

    # Get the voice list using the fixed method
    voice_list = manager.services[cloudlanguagetools.constants.Service.ElevenLabs.name].get_tts_voice_list()

    # Check the underlying API data
    service = manager.services[cloudlanguagetools.constants.Service.ElevenLabs.name]
    headers = service.get_headers()

    # Get raw API response
    url = "https://api.elevenlabs.io/v1/voices"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    all_voices_data = response.json()

    # Count voices by category in raw API response
    premade_count = sum(1 for v in all_voices_data['voices'] if v.get('category') == 'premade')
    professional_count = sum(1 for v in all_voices_data['voices'] if v.get('category') == 'professional')
    total_count = len(all_voices_data['voices'])

    print("=" * 80)
    print("ElevenLabs Voice Filtering Test")
    print("=" * 80)
    print(f"Raw API response statistics:")
    print(f"  Total voices: {total_count}")
    print(f"  Premade voices: {premade_count}")
    print(f"  Professional voices: {professional_count}")

    # Get models
    url = "https://api.elevenlabs.io/v1/models"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    model_data = response.json()
    model_data = [model for model in model_data if model['can_do_text_to_speech']]

    # Calculate expected voice count
    # Each premade voice should appear once for each model/language combination
    total_languages = sum(len(model['languages']) for model in model_data)
    expected_count = premade_count * total_languages

    print(f"\nModels and languages:")
    for model in model_data:
        print(f"  {model['name']}: {len(model['languages'])} languages")

    print(f"\nExpected voice count after filtering:")
    print(f"  {premade_count} premade voices × {total_languages} model/language combinations = {expected_count}")

    print(f"\nActual voice count from get_tts_voice_list(): {len(voice_list)}")

    # Verify all voices are premade
    print("\nVerifying first 5 voices are all premade:")
    for i, voice in enumerate(voice_list[:5]):
        print(f"  {i+1}. {voice.get_voice_shortname()}")

    if len(voice_list) == expected_count:
        print("\n✓ SUCCESS: Voice filtering is working correctly!")
    else:
        print(f"\n✗ ERROR: Expected {expected_count} voices but got {len(voice_list)}")

def test_elevenlabs_api_categories():
    """Test ElevenLabs API to see what voices are returned with different category filters"""
    config = cloudlanguagetools.encryption.decrypt()
    api_key = config['ElevenLabs']['api_key']

    headers = {
        "Accept": "application/json",
        "xi-api-key": api_key
    }

    # Test with category=premade
    print("=" * 80)
    print("Testing with category=premade")
    print("=" * 80)
    url_premade = "https://api.elevenlabs.io/v1/voices?category=premade"
    response = requests.get(url_premade, headers=headers)
    response.raise_for_status()
    data_premade = response.json()

    print(f"Total voices with premade filter: {len(data_premade['voices'])}")
    for voice in data_premade['voices'][:5]:  # Show first 5 voices
        print(f"  - {voice['name']} (ID: {voice['voice_id']}, Category: {voice.get('category', 'N/A')})")
        if 'labels' in voice:
            print(f"    Labels: {voice['labels']}")

    # Test without category filter
    print("\n" + "=" * 80)
    print("Testing without category filter")
    print("=" * 80)
    url_all = "https://api.elevenlabs.io/v1/voices"
    response = requests.get(url_all, headers=headers)
    response.raise_for_status()
    data_all = response.json()

    print(f"Total voices without filter: {len(data_all['voices'])}")

    # Analyze categories present in the data
    categories = {}
    for voice in data_all['voices']:
        category = voice.get('category', 'no_category')
        if category not in categories:
            categories[category] = []
        categories[category].append(voice['name'])

    print(f"\nCategories found in all voices:")
    for cat, voices in categories.items():
        print(f"  - {cat}: {len(voices)} voices")
        if len(voices) <= 3:
            for v in voices:
                print(f"      * {v}")

    # Check what categories are in the "premade" filtered response
    print("\nCategories in 'premade' filtered response:")
    premade_categories = {}
    for voice in data_premade['voices']:
        category = voice.get('category', 'no_category')
        if category not in premade_categories:
            premade_categories[category] = []
        premade_categories[category].append(voice['name'])

    for cat, voices in premade_categories.items():
        print(f"  - {cat}: {len(voices)} voices")
        if cat == 'professional':
            print(f"    First 3 professional voices: {voices[:3]}")

    # Check if premade voices are actually filtered
    premade_ids = {v['voice_id'] for v in data_premade['voices']}
    all_ids = {v['voice_id'] for v in data_all['voices']}

    print(f"\nVoices in 'premade' but not in 'all': {len(premade_ids - all_ids)}")
    print(f"Voices in 'all' but not in 'premade': {len(all_ids - premade_ids)}")

    # Show some non-premade voices
    non_premade = [v for v in data_all['voices'] if v['voice_id'] not in premade_ids]
    if non_premade:
        print(f"\nExamples of non-premade voices (first 5):")
        for voice in non_premade[:5]:
            print(f"  - {voice['name']} (Category: {voice.get('category', 'N/A')})")
            if 'labels' in voice:
                print(f"    Labels: {voice['labels']}")

    # Test other category values and parameter variations
    print("\n" + "=" * 80)
    print("Testing other category values and parameter variations")
    print("=" * 80)

    # Test different parameter variations
    test_urls = [
        ("category=cloned", "https://api.elevenlabs.io/v1/voices?category=cloned"),
        ("category=generated", "https://api.elevenlabs.io/v1/voices?category=generated"),
        ("category=professional", "https://api.elevenlabs.io/v1/voices?category=professional"),
        ("show_legacy=false", "https://api.elevenlabs.io/v1/voices?show_legacy=false"),
        ("category=premade&show_legacy=false", "https://api.elevenlabs.io/v1/voices?category=premade&show_legacy=false"),
    ]

    for param_desc, url_test in test_urls:
        try:
            response = requests.get(url_test, headers=headers)
            if response.status_code == 200:
                data_test = response.json()
                print(f"  {param_desc}: {len(data_test['voices'])} voices")
                # Check categories
                test_categories = set()
                for v in data_test['voices']:
                    test_categories.add(v.get('category', 'no_category'))
                print(f"    Categories present: {test_categories}")
            else:
                print(f"  {param_desc}: HTTP {response.status_code}")
        except Exception as e:
            print(f"  {param_desc}: Error - {e}")


def elevenlabs_api_test():
    config = cloudlanguagetools.encryption.decrypt()
    # pprint.pprint(config)
    api_key = config['ElevenLabs']['api_key']

    url = "https://api.elevenlabs.io/v1/models"

    headers = {
        "Accept": "application/json",
        "xi-api-key": api_key
    }

    response = requests.get(url, headers=headers)
    pprint.pprint(response.json())

def get_elevenlabs_models():
    manager = get_manager()
    elevenlabs_service = manager.services[cloudlanguagetools.constants.Service.ElevenLabs.name]
    headers = elevenlabs_service.get_headers()

    url = "https://api.elevenlabs.io/v1/models"
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()
    pprint.pprint(data)

def list_elevenlabs_voices():
    manager = get_manager()
    elevenlabs_service = manager.services[cloudlanguagetools.constants.Service.ElevenLabs.name]
    headers = elevenlabs_service.get_headers()

    # Use the same URL pattern as in elevenlabs.py (though the filter doesn't work on API side)
    url = "https://api.elevenlabs.io/v1/voices?category=premade"
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()
    all_voices = data.get('voices', [])

    # Filter to only include premade voices (API doesn't respect the category parameter)
    premade_voices = [voice for voice in all_voices if voice.get('category') == 'premade']

    print(f"Total voices returned by API: {len(all_voices)}")
    print(f"Premade voices (filtered): {len(premade_voices)}")
    print("\nPremade voice names:")
    for voice in premade_voices:
        print(f"  - {voice['name']}")

    # Also show categories breakdown for all voices
    categories = {}
    for voice in all_voices:
        category = voice.get('category', 'no_category')
        if category not in categories:
            categories[category] = []
        categories[category].append(voice['name'])

    print(f"\nAll voices by category:")
    for category, voice_names in categories.items():
        print(f"  {category}: {len(voice_names)} voices")

def test_elevenlabs_v3_params():
    """Test ElevenLabs v3 model stability parameter restrictions"""
    manager = get_manager()
    elevenlabs_service = manager.services[cloudlanguagetools.constants.Service.ElevenLabs.name]

    # Get models first to check what's available
    models = get_elevenlabs_models()

    # Test v3 stability values
    text = "Test"
    v3_stability_values = [0.0, 0.5, 1.0]  # Valid v3 values according to error message

    for stability in v3_stability_values:
        print(f"\nTesting stability {stability} with v3 model...")
        voice_key = {
            'voice_id': 'FGY2WhTYpPnrIDTdsKH5',  # From the error log
            'model_id': 'eleven_v3'
        }
        options = {
            'stability': stability,
            'similarity_boost': 0.75  # Keep this as is for now
        }

        try:
            result = elevenlabs_service.get_tts_audio(text, voice_key, options)
            print(f"✓ Stability {stability} works with v3")
        except Exception as e:
            print(f"✗ Stability {stability} failed: {e}")

def get_voice_list():
    manager = get_manager()
    tts_voice_list_json = manager.get_tts_voice_list_json()
    # print(tts_voice_list_json)
    output_filename = 'temp_data_files/voicelist.json'
    with open(output_filename, 'w', encoding='utf8') as f:
        f.write(json.dumps(tts_voice_list_json, indent=4, sort_keys=True, ensure_ascii=False))
        f.close()
    print(f'wrote {output_filename}')

def get_azure_voice_list():
    manager = get_manager()
    azure_service = manager.services[cloudlanguagetools.constants.Service.Azure.name]
    token = azure_service.get_token()

    base_url = f'https://{azure_service.region}.tts.speech.microsoft.com/'
    path = 'cognitiveservices/voices/list'
    constructed_url = base_url + path
    headers = {
        'Authorization': 'Bearer ' + token,
    }
    response = requests.get(constructed_url, headers=headers)
    response.raise_for_status()

    data = response.json()

    # print(data)
    output_filename = 'azure_voice_list.json'
    with open(output_filename, 'w') as f:
        f.write(json.dumps(data, sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': ')))
        f.close()
    print(f'wrote output to {output_filename}')

def get_voice_list_awesometts():
    # for awesometts
    manager = get_manager()
    tts_voice_list = manager.get_tts_voice_list_json()
    output_filename = 'temp_data_files/voicelist.py'
    #processed_voice_list = [x.python_obj() for x in tts_voice_list]
    with open(output_filename, 'w', encoding='utf8') as f:
        list_formatted = pprint.pformat(tts_voice_list, width=250)
        f.write('VOICE_LIST = ')
        f.write(list_formatted)
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

def get_transliteration_language_list():
    manager = get_manager()
    language_list_json = manager.get_transliteration_language_list_json()
    #print(tts_voice_list_json)
    output_filename = 'temp_data_files/transliteration_language_list.json'
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


def get_azure_transliteration_languages():
    manager = get_manager()
    data = manager.services[cloudlanguagetools.constants.Service.Azure.name].get_supported_languages()
    with open('temp_data_files/azure_transliteration_languages.json', 'w') as json_file:
        json.dump(data['transliteration'], json_file, indent=4)

    # [option.json_obj() for option in transliteration_language_list]

    data = manager.services[cloudlanguagetools.constants.Service.Azure.name].get_transliteration_language_list()
    json_data = [option.json_obj() for option in data]
    with open('temp_data_files/azure_transliteration_services.json', 'w') as json_file:
        json.dump(json_data, json_file, indent=4)
    # azure_data = self.get_supported_languages()
    # # print(data)
    # output_filename = 'azure_transliteration_languages.json'
    # with open(output_filename, 'w') as f:
    #     f.write(json.dumps(data, sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': ')))
    #     f.close()
    # print(f'wrote output to {output_filename}')


def get_google_translation_languages():
    manager = get_manager()
    data = manager.services[cloudlanguagetools.constants.Service.Google.name].get_translation_languages()
    # print(data)
    output_filename = 'temp_data_files/google_translation_languages.json'
    with open(output_filename, 'w') as f:
        f.write(json.dumps(data, sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': ')))
        f.close()
    print(f'wrote output to {output_filename}')


def get_watson_translation_languages():
    manager = get_manager()
    data = manager.services[cloudlanguagetools.constants.Service.Watson.name].get_translation_languages()
    # data = manager.services[cloudlanguagetools.constants.Service.Google.name].get_translation_language_list()
    # print(data)
    output_filename = 'temp_data_files/watson_translation_languages.json'
    with open(output_filename, 'w') as f:
        f.write(json.dumps(data, sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': ')))
        f.close()
    print(f'wrote output to {output_filename}')


if __name__ == '__main__':
    logger = logging.getLogger()
    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])
    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y%m%d-%H:%M:%S',
                        stream=sys.stdout,
                        level=logging.DEBUG)

    if len(sys.argv) > 1:
        function_name = sys.argv[1]
        if function_name in globals() and callable(globals()[function_name]):
            globals()[function_name]()
        else:
            print(f"Function '{function_name}' not found or not callable")
    else:
        print("Please provide a function name as the first argument")
