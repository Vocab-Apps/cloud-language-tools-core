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

import redisdb
import getcheddar_utils
import cloudlanguagetools.constants

# this test requires webhooks from getcheddar to go through

class GetCheddarEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(GetCheddarEndToEnd, cls).setUpClass()

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
        self.getcheddar_utils.create_test_customer(self.customer_code, self.customer_code, 'Test', 'Customer', 'SMALL')

        redis_getcheddar_user_key = self.redis_connection.build_key(redisdb.KEY_TYPE_GETCHEDDAR_USER, self.customer_code)
        max_wait_cycles = 25
        while not self.redis_connection.r.exists(redis_getcheddar_user_key) and max_wait_cycles > 0:
            time.sleep(0.1)
            max_wait_cycles -= 1
            logging.info('waiting for user key to get created')

        self.assertTrue(self.redis_connection.r.exists(redis_getcheddar_user_key))

        # finally, delete the user
        self.getcheddar_utils.delete_test_customer(self.customer_code)


if __name__ == '__main__':
    # how to run with logging on: pytest test_api.py -s -p no:logging -k test_translate
    unittest.main()  
