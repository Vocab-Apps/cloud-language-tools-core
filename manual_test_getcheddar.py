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


if __name__ == '__main__':
    # how to run with logging on: pytest test_api.py -s -p no:logging -k test_translate
    unittest.main()  
