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
import datetime
import time
import sys

import redisdb
import getcheddar_utils
import cloudlanguagetools.constants

# this test requires webhooks from getcheddar to go through

SLEEP_TIME = 0.1
MAX_WAIT_CYCLES = 25

class GetCheddarEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(GetCheddarEndToEnd, cls).setUpClass()

        logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                            datefmt='%Y%m%d-%H:%M:%S',
                            #stream=sys.stdout,
                            level=logging.DEBUG)        

        # url for cloud language tools
        cls.base_url = 'http://localhost:5000'
        cls.client_version = 'test'

        # setup redis connection
        cls.redis_connection = redisdb.RedisDb()
        cls.redis_connection.clear_db(wait=False)

        # helper classes
        cls.getcheddar_utils = getcheddar_utils.GetCheddarUtils()

        # build customer code
        timestamp = int(datetime.datetime.now().timestamp())
        cls.customer_code = f'languagetools+development.language_tools.customer-{timestamp}@mailc.net'


    @classmethod
    def tearDownClass(cls):
        pass


    def test_endtoend_1(self):
        # create a user
        # pytest manual_test_getcheddar.py -rPP -k test_endtoend_1
        print(self.customer_code)

        # create the user
        # ===============

        self.getcheddar_utils.create_test_customer(self.customer_code, self.customer_code, 'Test', 'Customer', 'SMALL')

        redis_getcheddar_user_key = self.redis_connection.build_key(redisdb.KEY_TYPE_GETCHEDDAR_USER, self.customer_code)
        max_wait_cycles = MAX_WAIT_CYCLES
        while not self.redis_connection.r.exists(redis_getcheddar_user_key) and max_wait_cycles > 0:
            time.sleep(SLEEP_TIME)
            max_wait_cycles -= 1

        # ensure redis keys got created correctly
        # ---------------------------------------

        self.assertTrue(self.redis_connection.r.exists(redis_getcheddar_user_key))
        api_key = self.redis_connection.r.get(redis_getcheddar_user_key)
        print(f'api_key: {api_key}')
        
        actual_user_data = self.redis_connection.get_getcheddar_user_data(self.customer_code)
        expected_user_data = {
            'type': 'getcheddar',
            'code': self.customer_code,
            'email': self.customer_code,
            'thousand_char_quota': 250,
            'thousand_char_overage_allowed': 0,
            'thousand_char_used': 0
        }
        self.assertEqual(actual_user_data, expected_user_data)

        # ensure we can retrieve some audio
        # ---------------------------------

        # get voice list
        response = requests.get(f'{self.base_url}/voice_list')
        voice_list = response.json()

        source_text_french = 'Je ne suis pas intéressé.'
        source_text_japanese = 'おはようございます'

        # get one azure voice for french

        service = 'Azure'
        french_voices = [x for x in voice_list if x['language_code'] == 'fr' and x['service'] == service]
        first_voice = french_voices[0]
        response = requests.post(f'{self.base_url}/audio_v2', json={
            'text': source_text_french,
            'service': service,
            'deck_name': 'french_deck_1',
            'request_mode': 'batch',
            'language_code': first_voice['language_code'],
            'voice_key': first_voice['voice_key'],
            'options': {}
        }, headers={'api_key': api_key, 'client': 'test', 'client_version': self.client_version})

        self.assertEqual(response.status_code, 200)

        # retrieve file
        output_temp_file = tempfile.NamedTemporaryFile()
        with open(output_temp_file.name, 'wb') as f:
            f.write(response.content)
        f.close()

        # perform checks on file
        # ----------------------

        # verify file type
        filetype = magic.from_file(output_temp_file.name)
        # should be an MP3 file
        expected_filetype = 'MPEG ADTS, layer III'        

        # finally, delete the user
        self.getcheddar_utils.delete_test_customer(self.customer_code)


if __name__ == '__main__':
    # how to run with logging on: pytest test_api.py -s -p no:logging -k test_translate
    unittest.main()  
