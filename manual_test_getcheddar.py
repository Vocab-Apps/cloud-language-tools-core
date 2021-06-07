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
                            stream=sys.stdout,
                            level=logging.DEBUG)        

        # setup redis connection
        cls.redis_connection = redisdb.RedisDb()
        cls.redis_connection.clear_db(wait=False)

        # helper classes
        cls.getcheddar_utils = getcheddar_utils.GetCheddarUtils()

        # build customer code
        timestamp = int(datetime.datetime.now().timestamp())
        cls.customer_code = f'languagetools+customer-{timestamp}@mailc.net'


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
        
        actual_user_data = self.redis_connection.get_getcheddar_user_data(self.customer_code)
        expected_user_data = {
            'code': self.customer_code,
            'email': self.customer_code,
            'thousand_char_quota': 250,
            'thousand_char_overage_allowed': 0,
            'thousand_char_used': 0
        }
        self.assertEqual(actual_user_data, expected_user_data)


        # finally, delete the user
        self.getcheddar_utils.delete_test_customer(self.customer_code)


if __name__ == '__main__':
    # how to run with logging on: pytest test_api.py -s -p no:logging -k test_translate
    unittest.main()  
