import unittest
import json
import tempfile
import magic
import datetime
import logging
import pytest
import quotas
import redisdb
from app import app, redis_connection
import cloudlanguagetools.constants

class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(ApiTests, cls).setUpClass()
        cls.client = app.test_client()
        redis_connection.clear_db(wait=False)
        
        # create new API key
        cls.api_key='test_key_01'
        redis_connection.add_test_api_key(cls.api_key, datetime.datetime.now() + datetime.timedelta(days=2))

        cls.api_key_expired='test_key_02_expired'
        redis_connection.add_test_api_key(cls.api_key_expired, datetime.datetime.now() + datetime.timedelta(days=-2))

        cls.api_key_over_quota='test_key_03_over_quota'
        redis_connection.add_test_api_key(cls.api_key_over_quota, datetime.datetime.now() + datetime.timedelta(days=2))        


    @classmethod
    def tearDownClass(cls):
        redis_connection.clear_db(wait=False)

    def test_verify_api_key(self):
        response = self.client.post('/verify_api_key', json={'api_key': self.api_key})
        data = json.loads(response.data)
        self.assertEqual({'key_valid': True, 'msg': 'API Key expires in 1 days'}, data)

        response = self.client.post('/verify_api_key', json={'api_key': self.api_key_expired})
        data = json.loads(response.data)
        self.assertEqual({'key_valid': False, 'msg': 'API Key expired'}, data)

        response = self.client.post('/verify_api_key', json={'api_key': 'ho ho ho'})
        data = json.loads(response.data)
        self.assertEqual({'key_valid': False, 'msg': 'API Key not valid'}, data)

    def test_language_list(self):
        response = self.client.get('/language_list')
        actual_language_list = json.loads(response.data) 
        self.assertTrue('fr' in actual_language_list)
        self.assertEqual(actual_language_list['fr'], 'French')
        self.assertEqual(actual_language_list['yue'], 'Chinese (Cantonese, Traditional)')
        self.assertEqual(actual_language_list['zh_cn'], 'Chinese (Simplified)')

    def test_voice_list(self):
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
        source_text = '成本很低'
        response = self.client.post('/translate_all', json={
            'text': source_text,
            'from_language': 'zh_cn',
            'to_language': 'fr'
        }, headers={'api_key': self.api_key})

        data = json.loads(response.data)
        self.assertEqual({
            'Amazon': 'Très faible coût',
            'Google': 'Coût très bas',
            'Azure': 'Le coût est faible',
            'Watson': 'Le coût est très bas.'
        }, data)

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

    def test_audio_overquota(self):
        # pytest test_api.py -rPP -k test_audio_overquota

        # increase the usage of that API key
        usage_slice = quotas.UsageSlice(cloudlanguagetools.constants.RequestType.audio,
                            cloudlanguagetools.constants.UsageScope.User, 
                            cloudlanguagetools.constants.UsagePeriod.daily, 
                            cloudlanguagetools.constants.Service.Naver, 
                            self.api_key_over_quota)
        usage_redis_key = redis_connection.build_key(redisdb.KEY_TYPE_USAGE, usage_slice.build_key_suffix())
        redis_connection.r.hincrby(usage_redis_key, 'characters', 19985)
        redis_connection.r.hincrby(usage_redis_key, 'requests', 1)

        response = self.client.get('/voice_list')
        voice_list = json.loads(response.data)
        service = 'Naver'
        english_voices = [x for x in voice_list if x['language_code'] == 'en' and x['service'] == service]
        first_voice = english_voices[0]

        # the first request should go through
        response = self.client.post('/audio', json={
            'text': 'Hello World',
            'service': service,
            'voice_key': first_voice['voice_key'],
            'options': {}
        }, headers={'api_key': self.api_key_over_quota})
        self.assertEqual(response.status_code, 200)

        # the second request should get blocked
        response = self.client.post('/audio', json={
            'text': 'Hello World 2',
            'service': service,
            'voice_key': first_voice['voice_key'],
            'options': {}
        }, headers={'api_key': self.api_key_over_quota})
        self.assertEqual(response.status_code, 429)



    @pytest.mark.skip(reason="only succeeds when quota is exceeded")
    def test_audio_naver_quota_exceeded(self):
        # pytest test_api.py -k test_audio_naver_quota_exceeded

        response = self.client.get('/voice_list')
        voice_list = json.loads(response.data)        
        service = 'Naver'
        french_voices = [x for x in voice_list if x['language_code'] == 'en' and x['service'] == service]
        first_voice = french_voices[0]

        response = self.client.post('/audio', json={
            'text': 'Hello World',
            'service': service,
            'voice_key': first_voice['voice_key'],
            'options': {}
        }, headers={'api_key': self.api_key})

        self.assertEqual(response.status_code, 400)
        error_response = json.loads(response.data)
        self.assertEqual(error_response['error'], 'Exceeded User daily quota')


    def test_audio_not_authenticated(self):
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
        })

        self.assertEqual(response.status_code, 401)
        

if __name__ == '__main__':
    # how to run with logging on: pytest test_api.py -s -p no:logging -k test_translate
    unittest.main()  
