import unittest
import quotas
import datetime

import redisdb
import cloudlanguagetools.constants

class TestApiKeys(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestApiKeys, cls).setUpClass()
        cls.redis_connection = redisdb.RedisDb()
        cls.redis_connection.clear_db(wait=False)

    @classmethod
    def tearDownClass(cls):
        cls.redis_connection.clear_db(wait=False)

    def test_add_patreon_key(self):
        api_key = self.redis_connection.password_generator()
        user_id = 42
        email = 'test@gmail.com'
        self.redis_connection.add_patreon_api_key(api_key, user_id, email)

        result = self.redis_connection.api_key_valid(api_key)
        self.assertEqual(result['key_valid'], True)

    def test_add_trial_key(self):
        api_key = self.redis_connection.password_generator()
        email = 'trialuser@gmail.com'
        self.redis_connection.add_trial_api_key(api_key, email, 10000)

        result = self.redis_connection.api_key_valid(api_key)
        self.assertEqual(result['key_valid'], True)        


    def test_add_test_key(self):
        api_key = self.redis_connection.password_generator()
        email = 'testuser@gmail.com'
        self.redis_connection.add_test_api_key(api_key)

        result = self.redis_connection.api_key_valid(api_key)
        self.assertEqual(result['key_valid'], True)


    def test_track_usage(self):
        api_key = self.redis_connection.password_generator()
        user_id = 43
        email = 'test43@gmail.com'
        self.redis_connection.add_patreon_api_key(api_key, user_id, email)

        service = cloudlanguagetools.constants.Service.Azure
        request_type = cloudlanguagetools.constants.RequestType.audio

        # this request should go through
        self.redis_connection.track_usage(api_key, service, request_type, 100)

        # this request will also go through but put us right under the limit
        self.redis_connection.track_usage(api_key, service, request_type, 79899)

        # this request will throw an exception
        self.assertRaises(cloudlanguagetools.errors.OverQuotaError, self.redis_connection.track_usage, api_key, service, request_type, 150)

