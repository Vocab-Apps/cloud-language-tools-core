import unittest
import quotas
import datetime

import redisdb
import cloudlanguagetools.constants

class TestApiKeys(unittest.TestCase):
    def setUp(self):
        self.redis_connection = redisdb.RedisDb()
        self.redis_connection.clear_db(wait=False)

    def tearDown(self):
        self.redis_connection.clear_db(wait=False)

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

    def test_get_patreon_user_key(self):
        user_id = 53
        email = 'user53@gmail.com'
        api_key_1 = self.redis_connection.get_patreon_user_key(user_id, email)

        result = self.redis_connection.api_key_valid(api_key_1)
        self.assertEqual(result['key_valid'], True)

        # request api key for the same user, should be the same
        api_key_2 = self.redis_connection.get_patreon_user_key(user_id, email)
        self.assertEqual(api_key_1, api_key_2)

        user_id = 54
        email = 'user54@gmail.com'
        api_key_3 = self.redis_connection.get_patreon_user_key(user_id, email)
        self.assertNotEqual(api_key_2, api_key_3)

    def test_get_trial_user_key(self):
        email = 'user55@gmail.com'
        api_key_1 = self.redis_connection.get_trial_user_key(email)

        result = self.redis_connection.api_key_valid(api_key_1)
        self.assertEqual(result['key_valid'], True)

        api_key_2 = self.redis_connection.get_trial_user_key(email)

        self.assertEqual(api_key_1, api_key_2)

        email = 'user56@gmail.com'
        api_key_3 = self.redis_connection.get_trial_user_key(email)        

        self.assertNotEqual(api_key_2, api_key_3)

    def test_track_usage(self):
        user_id = 43
        email = 'test43@gmail.com'
        api_key = self.redis_connection.get_patreon_user_key(user_id, email)

        service = cloudlanguagetools.constants.Service.Azure
        request_type = cloudlanguagetools.constants.RequestType.audio

        # this request should go through
        self.redis_connection.track_usage(api_key, service, request_type, 100)

        # this request will also go through but put us right under the limit
        self.redis_connection.track_usage(api_key, service, request_type, quotas.PATREON_MONTHLY_CHARACTER_LIMIT - 101)

        # this request will throw an exception
        self.assertRaises(cloudlanguagetools.errors.OverQuotaError, self.redis_connection.track_usage, api_key, service, request_type, 150)

    def test_track_usage_trial(self):
        email = 'trial_user_42@gmail.com'
        api_key = self.redis_connection.get_trial_user_key(email)

        service = cloudlanguagetools.constants.Service.Azure
        request_type = cloudlanguagetools.constants.RequestType.audio

        # this request should go through
        self.redis_connection.track_usage(api_key, service, request_type, 100)

        # this request will also go through but put us right under the limit
        self.redis_connection.track_usage(api_key, service, request_type, 9899)

        # this request will throw an exception
        self.assertRaises(cloudlanguagetools.errors.OverQuotaError, self.redis_connection.track_usage, api_key, service, request_type, 150)

        # increase this user's limit
        self.redis_connection.increase_trial_key_limit(email, 100000)
        # this request should go through
        self.redis_connection.track_usage(api_key, service, request_type, 5200)

        



