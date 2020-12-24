import os
import time
import redis

ENV_VAR_REDIS_HOST = 'REDIS_HOST'
ENV_VAR_REDIS_PORT = 'REDIS_PORT'
ENV_VAR_REDIS_PASSWORD ='REDIS_PASSWORD'

KEY_TYPE_API_KEY = 'api_key'

class RedisDb():
    def __init__(self):
        redis_host = os.environ[ENV_VAR_REDIS_HOST]
        redis_port = os.environ[ENV_VAR_REDIS_PORT]
        redis_password = os.environ[ENV_VAR_REDIS_PASSWORD]

        self.r = redis.Redis(host=redis_host, port=redis_port, db=0, password=redis_password)

    def build_key(self, key_type, key):
        return f'clt:{key_type}:{key}'

    def add_api_key(self, api_key, key_type, owner):
        redis_key = self.build_key(KEY_TYPE_API_KEY, api_key)
        hash_value = {
            'key_type': key_type,
            'owner': owner
        }
        self.r.hmset(redis_key, hash_value)
        print(f'added {redis_key}: {hash_value}')

    def list_api_keys(self):
        pattern = self.build_key(KEY_TYPE_API_KEY, '*')
        cursor, keys = self.r.scan(match=pattern)
        for key in keys:
            print(key)
            key_data = r.hgetall(key)
            print(key_data)

    def list_all_keys(self):
        cursor, keys = self.r.scan()
        for key in keys:
            print(key)

    def clear_db(self):
        print('WARNING! going to remove all keys after 30s')
        time.sleep(15)
        print('WARNING! going to remove all keys after 15s')
        time.sleep(15)
        self.r.flushdb()
