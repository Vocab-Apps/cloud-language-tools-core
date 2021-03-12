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

