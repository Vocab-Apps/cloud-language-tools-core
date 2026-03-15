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


def print_all_languages():
    languages = [language for language in cloudlanguagetools.languages.Language]
    languages = sorted(languages, key = lambda x: x.lang_name)
    for entry in languages:
        print(f'{entry.name},{entry.lang_name}')

def print_all_audio_languages():
    languages = [language for language in cloudlanguagetools.languages.AudioLanguage]
    languages = sorted(languages, key = lambda x: x.audio_lang_name)
    for entry in languages:
        print(f'{entry.lang.name},{entry.name},{entry.audio_lang_name}')

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
    for audio_language in cloudlanguagetools.languages.AudioLanguage:
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


def azure_dictionary_lookup_list():
    manager = get_manager()
    result = manager.services[cloudlanguagetools.constants.Service.Azure.name].get_dictionary_lookup_list()


def dictionary_lookup_azure():
    text = '放松'
    manager = get_manager()
    result = manager.services[cloudlanguagetools.constants.Service.Azure.name].custom_dictionary_lookup(text, 'zh-Hans', 'en')
    pprint.pprint(result)

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

    target_language_enum = cloudlanguagetools.languages.Language.cs

    target_language_id = [x for x in languages_service if x['language_code'] == target_language_enum.name][0]['language_id']

    for text in field1_list:
        translated_text = manager.get_translation(text, service_wanted, field1_language_id, target_language_id)
        print(f'source: {text} translated: {translated_text}')


def cereproc_authentication():
    url = 'https://api.cerevoice.com/v2/auth'
    username = os.environ['CEREPROC_USERNAME']
    password = os.environ['CEREPROC_PASSWORD']
    combined = f'{username}:{password}'
    auth_string = base64.b64encode(combined.encode('utf-8')).decode('utf-8')
    headers = {'authorization': f'Basic {auth_string}'}

    response = requests.get(url, headers=headers)

    print(response.json())

    access_token = response.json().access_token

    voices_url = 'https://api.cerevoice.com/v2/voices'

    response = requests.get(voices_url, headers={'Authorization': f'Bearer {access_token}'})
    print(response.json())


def cereproc_tts_voice_list():
    manager = get_manager()
    voice_list = manager.services[cloudlanguagetools.constants.Service.CereProc.name].get_tts_voice_list()
    print(f'voices: {len(voice_list)}')


def test_epitran():
    epi = epitran.Epitran('eng-Latn')
    result = epi.transliterate('Hello my friends')
    print(result)


def create_epitran_mappings():
    language_map = {'aar-Latn': 'Afar',
        'amh-Ethi': 'Amharic',
        'ara-Arab': 'Arabic',
        'aze-Cyrl': 'Azerbaijani',
        'aze-Latn': 'Azerbaijani',
        'ben-Beng': 'Bengali',
        'ben-Beng-red': 'Bengali',
        'cat-Latn': 'Catalan',
        'ceb-Latn': 'Cebuano',
        'ckb-Arab': 'Sorani',
        'deu-Latn': 'German',
        'deu-Latn-np': 'German',
        'deu-Latn-nar': 'German',
        'eng-Latn': 'English',
        'fas-Arab': 'Farsi',
        'fra-Latn': 'French',
        'fra-Latn-np': 'French',
        'hau-Latn': 'Hausa',
        'hin-Deva': 'Hindi',
        'hun-Latn': 'Hungarian',
        'ilo-Latn': 'Ilocano',
        'ind-Latn': 'Indonesian',
        'ita-Latn': 'Italian',
        'jav-Latn': 'Javanese',
        'kaz-Cyrl': 'Kazakh',
        'kaz-Latn': 'Kazakh',
        'kin-Latn': 'Kinyarwanda',
        'kir-Arab': 'Kyrgyz',
        'kir-Cyrl': 'Kyrgyz',
        'kir-Latn': 'Kyrgyz',
        'kmr-Latn': 'Kurmanji',
        'lao-Laoo': 'Lao',
        'mar-Deva': 'Marathi',
        'mlt-Latn': 'Maltese',
        'mya-Mymr': 'Burmese',
        'msa-Latn': 'Malay',
        'nld-Latn': 'Dutch',
        'nya-Latn': 'Chichewa',
        'orm-Latn': 'Oromo',
        'pan-Guru': 'Punjabi',
        'pol-Latn': 'Polish',
        'por-Latn': 'Portuguese',
        'ron-Latn': 'Romanian',
        'rus-Cyrl': 'Russian',
        'sna-Latn': 'Shona',
        'som-Latn': 'Somali',
        'spa-Latn': 'Spanish',
        'swa-Latn': 'Swahili',
        'swe-Latn': 'Swedish',
        'tam-Taml': 'Tamil',
        'tel-Telu': 'Telugu',
        'tgk-Cyrl': 'Tajik',
        'tgl-Latn': 'Tagalog',
        'tha-Thai': 'Thai',
        'tir-Ethi': 'Tigrinya',
        'tpi-Latn': 'Tok Pisin',
        'tuk-Cyrl': 'Turkmen',
        'tuk-Latn': 'Turkmen',
        'tur-Latn': 'Turkish',
        'ukr-Cyrl': 'Ukrainian',
        'uig-Arab': 'Uyghur',
        'uzb-Cyrl': 'Uzbek',
        'uzb-Latn': 'Uzbek',
        'vie-Latn': 'Vietnamese',
        'xho-Latn': 'Xhosa',
        'yor-Latn': 'Yoruba',
        'zul-Latn': 'Zulu'}
    # print(language_map)

    clt_reverse_language_map = {}
    for language in cloudlanguagetools.languages.Language:
        clt_reverse_language_map[language.lang_name] = language

    print(clt_reverse_language_map)

    for language_key, language_name in language_map.items():
        if language_name in clt_reverse_language_map:
            # print(f'found: {language_name}')
            language_enum = clt_reverse_language_map[language_name]
            assignment = f"""EpitranTransliterationLanguage(cloudlanguagetools.constants.{language_enum}, '{language_key}'),"""
            print(assignment)

def test_debounce():
    import convertkit
    convertkit_client = convertkit.ConvertKit()
    # email = '4wstpt6hpu@cloud-mail.top'
    email = sys.argv[1]
    logging.info(f'calling debounce.io api on {email}')
    valid, reason = convertkit_client.check_email_valid(email)
    print(f'valid: {valid} reason: {reason}')

def load_vocalware_voices():
    f = open('temp_data_files/vocalware_languages.json')
    languages_content = f.read()
    languages = json.loads(languages_content)
    # pprint.pprint(languages)

    # build map of language name to enum
    language_enum_map = {}
    for language in cloudlanguagetools.languages.Language:
        language_enum_map[language.lang_name] = language

    # add some exceptions
    language_enum_map['Chinese'] = cloudlanguagetools.languages.Language.zh_cn
    language_enum_map['Bengali'] = cloudlanguagetools.languages.Language.bn
    language_enum_map['Malaylam'] = cloudlanguagetools.languages.Language.ml
    language_enum_map['Portuguese'] = cloudlanguagetools.languages.Language.pt_pt
    language_enum_map['Slovanian'] = cloudlanguagetools.languages.Language.sl
    language_enum_map['Valencian'] = cloudlanguagetools.languages.Language.ca
    # print(language_enum_map)

    vocalware_language_id_to_language_enum = {}
    for entry in languages['LANGUAGELIST']['LANGUAGE']:
        language_name = entry['@NAME']
        language_id = int(entry['@ID'])
        # print(f'language_id: {language_id} language_name: {language_name}')
        if language_name in language_enum_map:
            lang_enum = language_enum_map[language_name]
            vocalware_language_id_to_language_enum[language_id] = lang_enum
        else:
            logging.error(f'language not found: {language_name}')

    print(vocalware_language_id_to_language_enum)

    language_to_audio_language_map = {}
    for audio_language in cloudlanguagetools.languages.AudioLanguage:
        language_to_audio_language_map[audio_language.lang] = audio_language


    f = open('temp_data_files/vocalware_voices.json')
    voices_content = f.read()
    voices = json.loads(voices_content)
    # pprint.pprint(voices)

    voice_list = voices['VOICELIST']['VOICE']
    # pprint.pprint(voice_list)

    pandas.set_option('display.max_rows', 999)
    voices_df = pandas.DataFrame(voice_list)
    voices_df['engine_id'] = voices_df['@ENGINE'].astype(int)
    # voices_subset_df = voices_df[~voices_df['engine_id'].isin([21, 22])]
    voices_subset_df = voices_df[voices_df['engine_id'].isin([2, 3, 7])]

    # print(voices_subset_df)

    audio_language_substr_mappings = {
        'Cantonese': cloudlanguagetools.languages.AudioLanguage.zh_HK,
        'Brazilian': cloudlanguagetools.languages.AudioLanguage.pt_BR,
        'Brasilian': cloudlanguagetools.languages.AudioLanguage.pt_BR,
        'Portugal': cloudlanguagetools.languages.AudioLanguage.pt_PT,
        'Canadian': cloudlanguagetools.languages.AudioLanguage.fr_CA,
        'Taiwanese': cloudlanguagetools.languages.AudioLanguage.zh_TW,
        'US': cloudlanguagetools.languages.AudioLanguage.en_US,
        'UK': cloudlanguagetools.languages.AudioLanguage.en_GB,
        'Australian': cloudlanguagetools.languages.AudioLanguage.en_AU,
        'Indian': cloudlanguagetools.languages.AudioLanguage.en_IN,
        'Castilian': cloudlanguagetools.languages.AudioLanguage.es_ES,
        'Chilean': cloudlanguagetools.languages.AudioLanguage.es_LA,
        'Argentine': cloudlanguagetools.languages.AudioLanguage.es_LA,
        'Mexican': cloudlanguagetools.languages.AudioLanguage.es_MX,
    }

    # voices_subset_df = voices_subset_df.head(5)

    gender_api_key = os.environ['GENDER_API_KEY']

    vocalware_voice_file = open('temp_data_files/vocalware_voices.py', 'w')
    for index, row in voices_subset_df.iterrows():
        voice_name = row['@NAME']
        voice_id = int(row['@ID'])
        language_id = int(row['@LANG'])
        engine_id = row['engine_id']

        if language_id != 0:
            language_enum = vocalware_language_id_to_language_enum[language_id]
            audio_language_enum = language_to_audio_language_map[language_enum]
            for key, value in audio_language_substr_mappings.items():
                if key in voice_name:
                    audio_language_enum = value
                    break
            # print(f'name: {voice_name} audio_language: {audio_language_enum} language_id: {language_id} voice_id: {voice_id} engine_id: {engine_id}')
            voice_name = re.sub('\(.*\)', '', voice_name)
            voice_name = voice_name.strip()
            # https://gender-api.com/get?name=elizabeth&key=afwY7pbzKjAJJxUL8AKzRzCVQujWLyuNN9ES
            print(f'processing voice {voice_name}')
            response = requests.get(f'https://gender-api.com/get?name={voice_name}&key={gender_api_key}')
            response_data = response.json()
            gender_response = response_data['gender']
            if gender_response == 'unknown':
                logging.error(f'could not detect gender for {voice_name}')
                gender_response = 'male'
            gender = cloudlanguagetools.constants.Gender[gender_response.Capitalize()]
            voice_code = f"""VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.{audio_language_enum.name}, '{voice_name}', cloudlanguagetools.constants.Gender.{gender.name}, {language_id}, {voice_id}, {engine_id}),\n"""
            vocalware_voice_file.write(voice_code)

    vocalware_voice_file.close()

def thai_tokenization():
    manager = get_manager()
    pythainlp_service = manager.services[cloudlanguagetools.constants.Service.PyThaiNLP.name]
    azure_service = manager.services[cloudlanguagetools.constants.Service.Azure.name]

    text = 'รถแท็กซี่อยู่ที่หน้าโรงแรมค่ะ'

    tokenized_result = pythainlp_service.tokenize(text, {})
    tokenized_result = [token for token in tokenized_result if len(token.strip()) > 0]

    if False:
        tokenized_result = [
            'ขอโทษ',
            'ครับ',
            'ช่วย',
            'พูด',
            'ช้าๆ',
            'ได้ไหม',
            'ครับ'
        ]

    print(tokenized_result)

    breakdown_entries = []
    for token in tokenized_result:
        romanization = pythainlp_service.get_transliteration(token, {})
        dictionary_lookup_result = azure_service.dictionary_lookup(token, 'th', 'en')
        translation = azure_service.get_translation(token, 'th', 'en')

        breakdown_entries.append({
            'token': token,
            'transliteration':  romanization,
            'dictionary_lookups': dictionary_lookup_result,
            'translation': translation
        })

    # pprint.pprint(breakdown_entries)

    def format_entry(entry):
        # do we have dictionary lookups ?
        token = entry['token']
        transliteration = entry['transliteration']

        translation = entry['translation']
        dictionary_lookups = entry['dictionary_lookups']

        meanings = [translation] + dictionary_lookups

        result = f"{token} <b>{transliteration}</b>: {' / '.join(meanings)}"
        return result

    html_entries = [format_entry(x) for x in breakdown_entries]

    html_text = '<br/>\n'.join(html_entries)
    output_filename = 'temp_data_files/breakdown.html'
    with open(output_filename, 'w', encoding='utf8') as f:
        f.write(html_text)
        f.close()
    logging.info(f'wrote {output_filename}')

def test_get_language_data():
    manager = get_manager()
    language_data = manager.get_language_data_json()
    output_filename = 'temp_data_files/language_data_v1.json'
    with open(output_filename, 'w', encoding='utf8') as f:
        f.write(json.dumps(language_data, indent=4, sort_keys=True, ensure_ascii=False))
        f.close()
    logging.info(f'wrote {output_filename}')

def test_get_language_data_redis():
    redis_connection = redisdb.RedisDb()
    language_data = redis_connection.get_language_data()
    output_filename = 'temp_data_files/language_data_redis.json'
    with open(output_filename, 'w', encoding='utf8') as f:
        f.write(json.dumps(language_data, indent=4, sort_keys=True, ensure_ascii=False))
        f.close()
    logging.info(f'wrote {output_filename}')

def test_voicen():

    import requests
    import json

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Token $VOICEN_ACCESS_TOKEN',
    }

    data = '{"text":"salam", "lang":"az", "voice_id": "325640"}'

    response = requests.post('https://tts.voicen.com/api/v1/jobs/text/', headers=headers, data=data)

    print(json.dumps(response.json(), indent=4, sort_keys=True))

def test_wenlin_lookup():
    manager = get_manager()
    wenlin_service = manager.services[cloudlanguagetools.constants.Service.Wenlin.name]

    lookup_result = wenlin_service.get_dictionary_lookup('仓库', {})
    print(lookup_result)
    lookup_result = wenlin_service.get_dictionary_lookup('啊', {})
    print(lookup_result)

def openai_test():
    from openai import AzureOpenAI

    # client = AzureOpenAI(api_key=os.getenv("OPENAI_API_KEY"),
    # azure_endpoint=azure_openai_config['azure_endpoint'],
    # api_version="2023-05-15",
    # api_key=azure_openai_config['azure_api_key'],
    # api_key=azure_openai_config['api_key'],
    # api_key=azure_openai_config['api_key'],
    # api_key=openai_config['api_key'],
    # api_key=openai_config['api_key'],
    # api_key=openai_config['api_key'])

    # Load your API key from an environment variable or secret management service

    list_models = False
    if list_models:
        models = client.models.list()
        model_id_list = [model['id'] for model in models.data]
        print(f'models: {model_id_list}')


    chat_completion = True
    if chat_completion:
        messages=[
                {"role": "system", "content": "You will translate and explain Thai text, showing a word by word breakdown with romanization"},
                {"role": "user", "content": "คนขับรถแท็กซี่: ถึงแล้วครับ 165 บาท ครับ"},
                {"role": "assistant", "content":
                """thai: คนขับรถแท็กซซี่ romanization: (khon khap rot taeksi): english: Taxi driver
thai: ถึงแล้วครับ romanization: (thueang laeo khap): english: Here we are, sir
thai: 165 บาท romanization: (nueng roi hok sip ha baht): english: 165 baht
thai: ครับ romanization: (khap): english: polite particle used by male speakers at the end of a sentence"""},
            ]

        messages = [
            {"role": 'user', 'content': 'When do we use this ? 大曬 (The attitude of "I\'m the boss!") provide some examples with jyutping'}
        ]

        messages = [
            {"role": 'user', 'content': 'Write funny and witty copy for someone to subscribe to AwesomeTTS Plus, a service to generate Japanese audio flashcards using Anki.'}
        ]

        # https://platform.openai.com/examples
        prompt = """Convert text toe programmatic command:

Example: Add the above text to Cantonese table
Output: add_above('Cantonese')

Example: Translate this to Japanese: 'blabla'
Output: translate('blabla', Japanese)

Example: Add French audio to Sound column
Output: add_audio(French, Sound)

Example: pronounce 'blala' in chinese
Ouput: pronounce('blala', chinese)

Put Chinese text to Mandarin table, add Mandarin audio to Pronunciation field, translate to italian: 'yo my friend'.

how to pronounce this in korean ? 'yaya'

Please put Cantonese text in Yue table.
"""

        # prompt = "can you explain the cultural significance of this Cantonese saying: 男尊女卑"

        #prompt = 'In the context of relationships, what does this Chinese sentence mean, and what is its litteral meaning ? 两个一起磨合'
#         prompt = """Write funny witty email in English to encourage someone to subscribe to an audio flashcard service called AwesomeTTS Plus, for making Language Learning audio flashcards.
# Include funny email subject line with emoji and email body and call to action on a button"""

        # prompt = 'Find funny and witty call to action in English, including an emoji, to encourage someone to subscribe to an audio flashcard service called AwesomeTTS Plus, for making Chinese language audio flashcards.'
        prompt = 'Write a joke about learning languages.'


        messages = [
            {'role': 'user', 'content': prompt}
        ]

        # https://platform.openai.com/docs/guides/chat
        # https://platform.openai.com/docs/guides/chat/introduction
        response = client.chat.completions.create(model="gpt-3.5-turbo",
        messages=messages)
        print(response)
        print(response.choices[0].message.content)

def microsoft_openai_test():
    #Note: The openai-python library support for Azure OpenAI is in preview.
    import os
    from openai import AzureOpenAI

    # client = AzureOpenAI(api_key=os.getenv("OPENAI_API_KEY"),
    # azure_endpoint=azure_openai_config['azure_endpoint'],
    # api_version="2023-05-15",
    # api_key=azure_openai_config['azure_api_key'],
    # api_key=azure_openai_config['api_key'],
    # api_key=azure_openai_config['api_key'],
    # api_key=openai_config['api_key'],
    # api_key=openai_config['api_key'],
    # api_key=openai_config['api_key'])

    azure_openai_config = cloudlanguagetools.encryption.decrypt()['OpenAI']


    deployment_name=azure_openai_config['azure_deployment_name'] #This will correspond to the custom name you chose for your deployment when you deployed a model.

    response = client.chat.completions.create(model=deployment_name, # engine = "deployment_name".
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Does Azure OpenAI support customer managed keys?"},
        {"role": "assistant", "content": "Yes, customer managed keys are supported by Azure OpenAI."},
        {"role": "user", "content": "Do other Azure Cognitive Services support this too?"}
    ])

    print(response)
    print(response.choices[0].message.content)

def openai_functioncalls_simple_example():
    from openai import AzureOpenAI

    # client = AzureOpenAI(api_key=os.getenv("OPENAI_API_KEY"),
    # azure_endpoint=azure_openai_config['azure_endpoint'],
    # api_version="2023-05-15",
    # api_key=azure_openai_config['azure_api_key'],
    # api_key=azure_openai_config['api_key'],
    # api_key=azure_openai_config['api_key'],
    # api_key=openai_config['api_key'],
    # api_key=openai_config['api_key'],
    # api_key=openai_config['api_key'])

    azure_openai_config = cloudlanguagetools.encryption.decrypt()['OpenAI']



    response = client.chat.completions.create(model="gpt-3.5-turbo-0613",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What's the weather in Miami?"},
    ],
    functions= [
        {
            'name': "getCityWeather",
            'description': "Get the weather in a given city",
            'parameters': {
                'type': "object",
                'properties': {
                'city': { 'type': "string", 'description': "The city" },
                'unit': { 'type': "string", 'enum': ["C", "F"] },
                },
                'required': ["city"],
            },
        },
    ],
    function_call= "auto")

    # print(response)
    # print(response['choices'][0]['message']['content'])
    pprint.pprint(response)

def openai_function_calls_telegram_bot():
    from openai import AzureOpenAI

    client = AzureOpenAI(api_key=os.getenv("OPENAI_API_KEY"),
    azure_endpoint=azure_openai_config['azure_endpoint'],
    api_version="2023-05-15")

    azure_openai_config = cloudlanguagetools.encryption.decrypt()['OpenAI']



    response = client.chat.completions.create(model="gpt-3.5-turbo-0613",
    messages=[
        {"role": "system", "content": "You are a helpful assistant specialized in translation. "},
        # {"role": "system", "content": "When I give you a French sentence, I want you to translate it to English, and also pronounce the audio."},
        # {"role": "system", "content": "When I give you an English sentence, I want you to translate it to French, and also pronounce the audio."},
        # {"role": "system", "content": "When I give you a French sentence, I want you to translate it to English"},
        # {"role": "system", "content": "When I give you an English sentence, I want you to translate it to French"},
        {"role": "system", "content": "When I give you a French sentence, I want you to pronounce it"},
        {"role": "system", "content": "When I give you an English sentence, I want you to pronounce it"},
        {"role": "user", "content": "Bonjour mes amis"},
        # {"role": "user", "content": "Please also translate this sentence to English"},
    ],
    functions= [
        # {
        #     'name': "translate",
        #     'description': "Translate given text from one language to another",
        #     'parameters': {
        #         'type': "object",
        #         'properties': {
        #         'text': { 'type': "string", 'description': "The input text the user wishes to translate" },
        #         'source_language': { 'type': "string", 'description': 'the language to translate from', 'enum': ['fr', 'en'] },
        #         'target_language': { 'type': "string", 'description': 'the language to translate to', 'enum': ['fr', 'en'] },
        #         },
        #         'required': ['text', 'source_language', 'target_language'],
        #     },
        # },
        # {
        #     'name': "audio",
        #     'description': "Generate audio to pronounce given text, using text to speech",
        #     'parameters': {
        #         'type': "object",
        #         'properties': {
        #         'text': { 'type': "string", 'description': "The input text the user wishes to generate audio for" },
        #         'language': { 'type': "string", 'description': 'the language of the input text to be pronounced', 'enum': ['fr', 'en'] },
        #         },
        #         'required': ['text', 'language'],
        #     },
        # },
        # {
        #     'name': "translate_and_audio",
        #     'description': "Translate a sentence, and then pronounce it",
        #     'parameters': {
        #         'type': "object",
        #         'properties': {
        #         'text': { 'type': "string", 'description': "The input text the user wishes to generate audio for" },
        #         'source_language': { 'type': "string", 'description': 'the language of the input text to be translated', 'enum': ['fr', 'en'] },
        #         'target_language': { 'type': "string", 'description': 'the target language to pronounce in', 'enum': ['fr', 'en'] },
        #         },
        #         'required': ['text', 'source_language', 'target_language'],
        #     },
        # },
        {
            'name': "process_sentence",
            'description': "Process a sentence, by translating it and generating audio, depending on parameters",
            'parameters': {
                'type': "object",
                'properties': {
                    'text': { 'type': "string", 'description': "The input text the user wishes to generate audio for" },
                    'source_language': { 'type': "string", 'description': 'the language of the input text to be translated', 'enum': ['fr', 'en'] },
                    'target_language': { 'type': "string", 'description': 'the target language to pronounce in', 'enum': ['fr', 'en'] },
                    'translate': { 'type': "boolean", 'description': 'whether to translate the input text' },
                    'audio': { 'type': "boolean", 'description': 'whether to generate audio for the input text' },
                },
                'required': ['text', 'source_language', 'target_language', 'translate', 'audio'],
            },
        },
    ],
    function_call= "auto")

    # print(response)
    # print(response['choices'][0]['message']['content'])
    pprint.pprint(response)


def openai_detect_language():
    from openai import AzureOpenAI

    # client = AzureOpenAI(api_key=os.getenv("OPENAI_API_KEY"),
    # azure_endpoint=azure_openai_config['azure_endpoint'],
    # api_version="2023-05-15",
    # api_key=azure_openai_config['azure_api_key'],
    # api_key=azure_openai_config['api_key'],
    # api_key=azure_openai_config['api_key'],
    # api_key=openai_config['api_key'],
    # api_key=openai_config['api_key'],
    # api_key=openai_config['api_key'])

    manager = get_manager()

    openai_config = cloudlanguagetools.encryption.decrypt()['OpenAI']


    response = client.chat.completions.create(model="gpt-3.5-turbo-0613",
    messages=[
        {"role": "system", "content": "You are a helpful assistant specialized in translation. "},
        {"role": "system", "content": "Detect the language of the sentence provided"},
        {"role": "user", "content": "Bonjour mes amis"},
    ],
    functions= [
        {
            'name': "detect_language",
            'description': "Detect the language of input text",
            'parameters': {
                'type': "object",
                'properties': {
                    'text': { 'type': "string", 'description': "The input text the user wishes to generate audio for" },
                },
                'required': ['text'],
            },
        },
    ],
    function_call= "auto")

    def detect_language(text):
        return manager.detect_language([text])

    pprint.pprint(response)

    message = response.choices[0].message
    if message['function_call'] != None:
        function_name = message['function_call']['name']
        arguments = json.loads(message["function_call"]["arguments"])
        if function_name == 'detect_language':
            text = arguments['text']
            detected_language = detect_language(text)
            print(f'detected language: {detected_language}')

    # print(response)
    # print(response['choices'][0]['message']['content'])


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
