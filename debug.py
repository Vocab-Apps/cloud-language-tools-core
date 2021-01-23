import os
import base64
import json
import tempfile
import shutil 
import unittest
import pydub
import pydub.playback
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


def play_google_audio():
    manager = get_manager()

    service = 'Google'
    text = 'hello world test 1'

    voice_key = {
        'language_code': "en-GB",
        'name': "en-GB-Wavenet-A",
        'ssml_gender': "FEMALE"
    }    

    options = {'speaking_rate': 1.5} # 0.25 to 4.0
    options = {'pitch': 5} # -20.0 to 20.0
    result = manager.get_tts_audio(text, service, voice_key, options)
    filename = result.name
    music = pydub.AudioSegment.from_mp3(filename)
    pydub.playback.play(music)    

def play_azure_audio():
    manager = get_manager()

    service = 'Azure'
    text = 'hello world test 1'

    voice_key = {
        "name": "Microsoft Server Speech Text to Speech Voice (en-GB, MiaNeural)"
    }

    #options = {'speaking_rate': 1.5}
    #options = {'pitch': 5}
    # options = {'pitch': 100} # -100 to +100?
    options = {'rate': 3.0} # 0.5 to 3 ?
    result = manager.get_tts_audio(text, service, voice_key, options)
    filename = result.name
    music = pydub.AudioSegment.from_mp3(filename)
    pydub.playback.play(music)    

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

def get_voice_list():
    manager = get_manager()
    tts_voice_list_json = manager.get_tts_voice_list_json()
    # print(tts_voice_list_json)    
    output_filename = 'temp_data_files/voicelist.json'
    with open(output_filename, 'w', encoding='utf8') as f:
        f.write(json.dumps(tts_voice_list_json, indent=4, sort_keys=True, ensure_ascii=False))
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

def output_language_audio_mapping():
    language_map = {}
    for audio_language in cloudlanguagetools.constants.AudioLanguage:
        language = audio_language.lang
        if language not in language_map:
            language_map[language] = []
        language_map[language].append(audio_language)

    output_filename = 'temp_data_files/output_language_audio_mapping.txt'
    with open(output_filename, 'w') as f:
        for key, data in language_map.items():
            f.write(f'language: {key} ({key.lang_name})\n')
            for item in data:
                f.write(f'    audio language: {item} ({item.audio_lang_name})\n')
        f.close()
                

def detect_language():
    input_text = 'ผมจะไปประเทศไทยพรุ่งนี้ครับ'
    manager = get_manager()
    #manager.services[cloudlanguagetools.constants.Service.Azure.name].detect_language(input_text)
    manager.services[cloudlanguagetools.constants.Service.Google.name].detect_language(input_text)

def translate_google():
    text = 'Bonjour Madame'
    manager = get_manager()
    translated_text = manager.get_translation(text, 'Google', 'fr', 'cs')
    print(translated_text)

def translate_azure():
    text = 'Je suis un ours.'
    manager = get_manager()
    translated_text = manager.get_translation(text, 'Azure', 'fr', 'cs')
    print(translated_text)    

def transliterate_azure():
    text = 'Je suis un ours.'
    manager = get_manager()
    service = manager.services[cloudlanguagetools.constants.Service.Azure.name]
    test_thai = True
    text = 'ผมจะไปประเทศไทยพรุ่งนี้ครับ'
    text = 'ผม | จะ | ไป | ประเทศไทย | พรุ่ง | นี้ | ครับ'
    language_key = 'th'
    from_script = 'Thai'
    to_script = 'Latn'
    result = service.transliteration(text, language_key, from_script, to_script)
    print(result)



def dictionary_lookup_azure():
    text = '出事'
    manager = get_manager()
    manager.services[cloudlanguagetools.constants.Service.Azure.name].dictionary_lookup(text, 'zh-Hans', 'en')

def dictionary_examples_azure():
    text = '饥不择食'
    translated_text = 'beggars can\'t be choosers'
    manager = get_manager()
    manager.services[cloudlanguagetools.constants.Service.Azure.name].dictionary_examples(text, translated_text, 'en', 'zh-Hans')    

def end_to_end_test():
    field1_list = [
        'Pouvez-vous me faire le change ?',
        'Pouvez-vous débarrasser la table, s\'il vous plaît?',
        'Je ne suis pas intéressé.'
    ]    
    field2_list = [
        'Can you change money for me?',
        'Can you please clear the plates?',
        'I\'m not interested.'
    ]
    # step 1: recognize languages
    manager = get_manager()
    language1 = manager.detect_language(field1_list)
    print(language1)
    language2 = manager.detect_language(field2_list)
    print(language2)

    # step2 retrieve list of languages supported for translation
    translation_language_list = manager.get_translation_language_list_json()

    service_wanted = 'Google'
    languages_service = [x for x in translation_language_list if x['service'] == service_wanted]

    field1_language_id = [x for x in languages_service if x['language_code'] == language1.name][0]['language_id']
    field2_language_id = [x for x in languages_service if x['language_code'] == language2.name][0]['language_id']

    target_language_enum = cloudlanguagetools.constants.Language.cs

    target_language_id = [x for x in languages_service if x['language_code'] == target_language_enum.name][0]['language_id']

    for text in field1_list:
        translated_text = manager.get_translation(text, service_wanted, field1_language_id, target_language_id)
        print(f'source: {text} translated: {translated_text}')
    



if __name__ == '__main__':
    # test_azure_audio()
    # test_google_audio()
    # play_google_audio()
    # play_azure_audio()
    get_voice_list()
    # get_watson_voice_list()
    # get_azure_translation_languages()
    # get_google_translation_languages()
    # get_watson_translation_languages()
    #output_languages_enum()
    #get_translation_language_list()
    # output_language_audio_mapping()
    # detect_language()
    # translate_google()
    # translate_azure()
    # dictionary_lookup_azure()
    # dictionary_examples_azure()
    # end_to_end_test()
    # transliterate_azure()
    # get_transliteration_language_list()