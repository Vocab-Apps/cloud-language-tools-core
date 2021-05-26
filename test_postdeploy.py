import unittest
import json
import tempfile
import magic
import datetime
import logging
import pytest
import os
import requests
import urllib.parse
import cloudlanguagetools.constants

class PostDeployTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(PostDeployTests, cls).setUpClass()

        cls.base_url = os.environ['ANKI_LANGUAGE_TOOLS_BASE_URL']
        cls.api_key=os.environ['ANKI_LANGUAGE_TOOLS_API_KEY']
        cls.client_version = 'v0.01'

    @classmethod
    def tearDownClass(cls):
        pass

    def get_url(self, path):
        return f'{self.base_url}{path}'

    def test_verify_api_key(self):
        # pytest test_postdeploy.py -rPP -k test_verify_api_key
        response = requests.post(self.get_url('/verify_api_key'), json={'api_key': self.api_key})
        data = response.json()
        self.assertEqual({'key_valid': True, 'msg': 'API Key is valid'}, data)


    def test_language_list(self):
        response = self.client.get('/language_list')
        actual_language_list = json.loads(response.data) 
        self.assertTrue('fr' in actual_language_list)
        self.assertEqual(actual_language_list['fr'], 'French')
        self.assertEqual(actual_language_list['yue'], 'Chinese (Cantonese, Traditional)')
        self.assertEqual(actual_language_list['zh_cn'], 'Chinese (Simplified)')

    def test_voice_list(self):
        # pytest test_api.py -rPP -k 'test_voice_list'

        response = self.client.get('/voice_list')
        voice_list = json.loads(response.data)
        self.assertTrue(len(voice_list) > 100) # with google and azure, we already have 400 voices or so
        
        subset_1 = [x for x in voice_list if x['language_code'] == 'fr']
        self.assertTrue(len(subset_1) > 10) # there should be a dozen french voices

        voice1 = subset_1[0]

        self.assertTrue(len(voice1['gender']) > 0)
        self.assertTrue(len(voice1['language_code']) > 0)
        self.assertTrue(len(voice1['audio_language_code']) > 0)
        self.assertTrue(len(voice1['audio_language_name']) > 0)
        self.assertTrue(len(voice1['voice_description']) > 0)
        self.assertTrue(len(voice1['service']) > 0)
        self.assertTrue('voice_key' in voice1)

    def test_translation_language_list(self):
        # pytest test_api.py -rPP -k 'test_translation_language_list'
        response = self.client.get('/translation_language_list')
        translation_language_list = json.loads(response.data)
        self.assertTrue(len(translation_language_list) > 100) # with google and azure, we already have 400 voices or so
        
        subset_1 = [x for x in translation_language_list if x['language_code'] == 'fr']
        self.assertTrue(len(subset_1) >= 2) # at least one for google, one for azure

        language1 = subset_1[0]

        self.assertTrue(len(language1['language_code']) > 0)
        self.assertTrue(len(language1['language_id']) > 0)
        self.assertTrue(len(language1['language_name']) > 0)
        self.assertTrue(len(language1['service']) > 0)

    def test_transliteration_language_list(self):
        # pytest test_api.py -rPP -k 'test_transliteration_language_list'
        response = self.client.get('/transliteration_language_list')
        transliteration_language_list = json.loads(response.data)
        self.assertTrue(len(transliteration_language_list) > 30) # 
        
        subset_1 = [x for x in transliteration_language_list if x['language_code'] == 'zh_cn']
        self.assertTrue(len(subset_1) >= 1) # at least one, azure

        language1 = subset_1[0]

        self.assertTrue(len(language1['language_code']) > 0)
        self.assertTrue(len(language1['language_name']) > 0)
        self.assertTrue(len(language1['service']) > 0)
        self.assertTrue(len(language1['transliteration_name']) > 0)


    def test_translate(self):
        source_text = 'Je ne suis pas intéressé.'
        response = self.client.post('/translate', json={
            'text': source_text,
            'service': 'Azure',
            'from_language_key': 'fr',
            'to_language_key': 'en'
        }, headers={'api_key': self.api_key})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['translated_text'], "I'm not interested.")

        # locate the azure language_id for simplified chinese
        response = self.client.get('/translation_language_list')
        translation_language_list = json.loads(response.data)
        chinese_azure = [x for x in translation_language_list if x['language_code'] == 'zh_cn' and x['service'] == 'Azure']
        translation_azure_chinese = chinese_azure[0]

        response = self.client.post('/translate', json={
            'text': '中国有很多外国人',
            'service': 'Azure',
            'from_language_key': translation_azure_chinese['language_id'],
            'to_language_key': 'en'
        }, headers={'api_key': self.api_key})

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['translated_text'], 'There are many foreigners in China')

    def test_translate_not_authenticated(self):
        source_text = 'Je ne suis pas intéressé.'
        response = self.client.post('/translate', json={
            'text': source_text,
            'service': 'Azure',
            'from_language_key': 'fr',
            'to_language_key': 'en'
        })

        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data['error'], "API Key not valid")

        response = self.client.post('/translate', json={
            'text': '中国有很多外国人',
            'service': 'Azure',
            'from_language_key': 'zh-Hans',
            'to_language_key': 'en'
        }, headers={'api_key': self.api_key_expired})

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(data['error'], 'API Key expired')

    def test_translate_all(self):
        # pytest test_api.py -k test_translate_all
        source_text = '成本很低'
        response = self.client.post('/translate_all', json={
            'text': source_text,
            'from_language': 'zh_cn',
            'to_language': 'fr'
        }, headers={'api_key': self.api_key})

        data = json.loads(response.data)
        self.assertTrue(data['Azure'] == 'Le coût est faible' or data['Azure'] == 'Le coût est très faible')
        self.assertEqual(data['Amazon'], 'Très faible coût')
        self.assertEqual(data['Google'], 'À bas prix')
        self.assertEqual(data['Watson'], 'Le coût est très bas.')

    def test_translate_error(self):
        source_text = 'Je ne suis pas intéressé.'
        response = self.client.post('/translate', json={
            'text': source_text,
            'service': 'Azure',
            'from_language_key': 'fr',
            'to_language_key': 'zh_cn'
        }, headers={'api_key': self.api_key})

        self.assertEqual(response.status_code, 400)
        error_response = json.loads(response.data)
        error_message = error_response['error']
        self.assertTrue('The target language is not valid' in error_message)


    def test_transliteration(self):
        response = self.client.get('/transliteration_language_list')
        transliteration_language_list = json.loads(response.data)

        service = 'Azure'
        source_text = '成本很低'
        from_language = 'zh_cn'
        transliteration_candidates = [x for x in transliteration_language_list if x['language_code'] == from_language and x['service'] == service]
        self.assertTrue(len(transliteration_candidates) == 1) # once more services are introduced, change this
        transliteration_option = transliteration_candidates[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']

        response = self.client.post('/transliterate', json={
            'text': source_text,
            'service': service,
            'transliteration_key': transliteration_key
        }, headers={'api_key': self.api_key})

        result = json.loads(response.data)
        self.assertEqual({'transliterated_text': 'chéng běn hěn dī'}, result)

    def test_transliteration_mandarin_cantonese(self):
        response = self.client.get('/transliteration_language_list')
        transliteration_language_list = json.loads(response.data)

        service = 'MandarinCantonese'
        source_text = '成本很低'
        from_language = 'zh_cn'
        transliteration_candidates = [x for x in transliteration_language_list if x['language_code'] == from_language and x['service'] == service]
        self.assertTrue(len(transliteration_candidates) > 0) # once more services are introduced, change this

        # pick the one
        selected_candidate = [x for x in transliteration_candidates if '(Diacritics )' in x['transliteration_name']]
        self.assertTrue(len(selected_candidate) == 1)

        transliteration_option = selected_candidate[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']

        response = self.client.post('/transliterate', json={
            'text': source_text,
            'service': service,
            'transliteration_key': transliteration_key
        }, headers={'api_key': self.api_key})

        result = json.loads(response.data)
        self.assertEqual({'transliterated_text': 'chéngběn hěn dī'}, result)

    def test_transliteration_mandarin_cantonese_2(self):
        response = self.client.get('/transliteration_language_list')
        transliteration_language_list = json.loads(response.data)

        service = 'MandarinCantonese'
        source_text = '好多嘢要搞'
        from_language = 'yue'
        transliteration_candidates = [x for x in transliteration_language_list if x['language_code'] == from_language and x['service'] == service]
        self.assertTrue(len(transliteration_candidates) > 0) # once more services are introduced, change this

        # pick the one
        selected_candidate = [x for x in transliteration_candidates if '(Diacritics )' in x['transliteration_name']]
        self.assertTrue(len(selected_candidate) == 1)

        transliteration_option = selected_candidate[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']

        response = self.client.post('/transliterate', json={
            'text': source_text,
            'service': service,
            'transliteration_key': transliteration_key
        }, headers={'api_key': self.api_key})

        result = json.loads(response.data)
        self.assertEqual({'transliterated_text': 'hóudō jě jîu gáau'}, result)

    def test_transliteration_not_authenticated(self):
        response = self.client.get('/transliteration_language_list')
        transliteration_language_list = json.loads(response.data)

        service = 'Azure'
        source_text = '成本很低'
        from_language = 'zh_cn'
        transliteration_candidates = [x for x in transliteration_language_list if x['language_code'] == from_language and x['service'] == service]
        self.assertTrue(len(transliteration_candidates) == 1) # once more services are introduced, change this
        transliteration_option = transliteration_candidates[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']

        response = self.client.post('/transliterate', json={
            'text': source_text,
            'service': service,
            'transliteration_key': transliteration_key
        })

        self.assertEqual(response.status_code, 401)
        result = json.loads(response.data)
        self.assertEqual({'error': 'API Key not valid'}, result)

    def test_detection(self):
        source_list = [
            'Pouvez-vous me faire le change ?',
            'Pouvez-vous débarrasser la table, s\'il vous plaît?'
        ]

        response = self.client.post('/detect', json={
            'text_list': source_list
        }, headers={'api_key': self.api_key})

        data = json.loads(response.data)
        self.assertEqual(data['detected_language'], 'fr')

    def test_detection_not_authenticated(self):
        source_list = [
            'Pouvez-vous me faire le change ?',
            'Pouvez-vous débarrasser la table, s\'il vous plaît?'
        ]

        response = self.client.post('/detect', json={
            'text_list': source_list
        }, headers={'api_key': self.api_key_expired})

        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'API Key expired')

    def test_audio(self):
        # pytest test_api.py -k test_audio
        # get one azure voice for french
        response = self.client.get('/voice_list')
        voice_list = json.loads(response.data)        
        service = 'Azure'
        french_voices = [x for x in voice_list if x['language_code'] == 'fr' and x['service'] == service]
        first_voice = french_voices[0]

        response = self.client.post('/audio', json={
            'text': 'Je ne suis pas intéressé.',
            'service': service,
            'voice_key': first_voice['voice_key'],
            'options': {}
        }, headers={'api_key': self.api_key})

        self.assertEqual(response.status_code, 200)

        output_temp_file = tempfile.NamedTemporaryFile()
        with open(output_temp_file.name, 'wb') as f:
            f.write(response.data)
        f.close()

        # verify file type
        filetype = magic.from_file(output_temp_file.name)
        # should be an MP3 file
        expected_filetype = 'MPEG ADTS, layer III'

        self.assertTrue(expected_filetype in filetype)

    def test_audio_v2(self):
        # pytest test_api.py -k test_audio_v2


        source_text_french = 'Je ne suis pas intéressé.'
        source_text_japanese = 'おはようございます'

        # get one azure voice for french
        response = self.client.get('/voice_list')
        voice_list = json.loads(response.data)

        service = 'Azure'
        french_voices = [x for x in voice_list if x['language_code'] == 'fr' and x['service'] == service]
        first_voice = french_voices[0]
        response = self.client.post('/audio_v2', json={
            'text': source_text_french,
            'service': service,
            'deck_name': 'french_deck_1',
            'request_mode': 'batch',
            'language_code': first_voice['language_code'],
            'voice_key': first_voice['voice_key'],
            'options': {}
        }, headers={'api_key': self.api_key_v2, 'client': 'test', 'client_version': self.client_version})

        self.assertEqual(response.status_code, 200)

        # retrieve file
        output_temp_file = tempfile.NamedTemporaryFile()
        with open(output_temp_file.name, 'wb') as f:
            f.write(response.data)
        f.close()

        # perform checks on file
        # ----------------------

        # verify file type
        filetype = magic.from_file(output_temp_file.name)
        # should be an MP3 file
        expected_filetype = 'MPEG ADTS, layer III'

        self.assertTrue(expected_filetype in filetype)


    def test_audio_forvo_not_found(self):
        # pytest test_api.py -k test_audio_forvo_not_found
        
        # get one azure voice for french
        response = self.client.get('/voice_list')
        voice_list = json.loads(response.data)        
        service = 'Forvo'
        french_voices = [x for x in voice_list if x['language_code'] == 'fr' and x['service'] == service]
        first_voice = french_voices[0]

        response = self.client.post('/audio', json={
            'text': 'wordnotfound',
            'service': service,
            'voice_key': first_voice['voice_key'],
            'options': {}
        }, headers={'api_key': self.api_key})

        self.assertEqual(response.status_code, 404)


    def test_audio_yomichan(self):
        # pytest test_api.py -rPP -k test_audio_yomichan
        
        # get one azure voice for japanese
        response = self.client.get('/voice_list')
        voice_list = json.loads(response.data)        
        service = 'Azure'
        japanese_voices = [x for x in voice_list if x['language_code'] == 'ja' and x['service'] == service]
        first_voice = japanese_voices[0]

        source_text = 'おはようございます'
        voice_key_str = urllib.parse.quote_plus(json.dumps(first_voice['voice_key']))
        url_params = f'api_key={self.api_key}&service={service}&voice_key={voice_key_str}&text={source_text}'
        url = f'/yomichan_audio?{url_params}'

        print(f'url: {url}')

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        output_temp_file = tempfile.NamedTemporaryFile()
        with open(output_temp_file.name, 'wb') as f:
            f.write(response.data)
        f.close()

        # verify file type
        filetype = magic.from_file(output_temp_file.name)
        # should be an MP3 file
        expected_filetype = 'MPEG ADTS, layer III'

        self.assertTrue(expected_filetype in filetype)

    def test_audio_yomichan_incorrect_api_key(self):
        # pytest test_api.py -rPP -k test_audio_yomichan_incorrect_api_key
        
        # get one azure voice for japanese
        response = self.client.get('/voice_list')
        voice_list = json.loads(response.data)        
        service = 'Azure'
        japanese_voices = [x for x in voice_list if x['language_code'] == 'ja' and x['service'] == service]
        first_voice = japanese_voices[0]

        source_text = 'おはようございます'
        voice_key_str = urllib.parse.quote_plus(json.dumps(first_voice['voice_key']))
        url_params = f'api_key=incorrectapikey&service={service}&voice_key={voice_key_str}&text={source_text}'
        url = f'/yomichan_audio?{url_params}'

        print(f'url: {url}')

        response = self.client.get(url)

        self.assertEqual(response.status_code, 401)

    def test_audio_not_authenticated(self):
        # get one azure voice for french
        response = requests.get(f'/voice_list')
        voice_list = json.loads(response.data)        
        service = 'Azure'
        french_voices = [x for x in voice_list if x['language_code'] == 'fr' and x['service'] == service]
        first_voice = french_voices[0]

        response = self.client.post('/audio', json={
            'text': 'Je ne suis pas intéressé.',
            'service': service,
            'voice_key': first_voice['voice_key'],
            'options': {}
        })

        self.assertEqual(response.status_code, 401)

    def test_audio_not_authenticated_v2(self):
        # pytest test_api.py -rPP -k test_audio_not_authenticated_v2

        response = self.client.get('/voice_list')
        voice_list = json.loads(response.data)        
        service = 'Azure'
        french_voices = [x for x in voice_list if x['language_code'] == 'fr' and x['service'] == service]
        first_voice = french_voices[0]

        response = self.client.post('/audio_v2', json={
            'text': 'Je ne suis pas intéressé.',
            'service': service,
            'voice_key': first_voice['voice_key'],
            'language_code': first_voice['language_code'],
            'options': {}
        })

        self.assertEqual(response.status_code, 401)        
        

if __name__ == '__main__':
    # how to run with logging on: pytest test_api.py -s -p no:logging -k test_translate
    unittest.main()  
