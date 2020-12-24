import os
import time
import datetime
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

    def add_api_key(self, api_key, key_type, owner, expiration_date):
        key_removal_date = expiration_date + datetime.timedelta(days=31)
        key_expiration_timestamp = int(expiration_date.timestamp())
        key_removal_timestamp_millis = int(key_removal_date.timestamp() * 1000.0)
        redis_key = self.build_key(KEY_TYPE_API_KEY, api_key)
        hash_value = {
            'key_type': key_type,
            'owner': owner,
            'expiration': key_expiration_timestamp,
        }
        self.r.hmset(redis_key, hash_value)
        self.r.expireat(redis_key, key_removal_timestamp_millis)

        print(f'added {redis_key}: {hash_value}, expiring at: {expiration_date}, removed at: {key_removal_date}')

    def api_key_valid(self, api_key):
        redis_key = self.build_key(KEY_TYPE_API_KEY, api_key)
        if self.r.exists(redis_key) == 0:
            return {'key_valid': False, 'msg': 'API Key not valid'}
        key_data = self.r.hgetall(redis_key)
        expiration = self.r.hget(redis_key, 'expiration')
        expiration_timestamp = int(self.r.hget(redis_key, 'expiration'))
        current_dt = datetime.datetime.now()
        current_timestamp = int(current_dt.timestamp())
        expiration_dt = datetime.datetime.fromtimestamp(expiration_timestamp)
        if expiration_timestamp > current_timestamp:
            expire_time_delta = expiration_dt - current_dt
            return {'key_valid': True, 'msg': f'API Key expires in {expire_time_delta.days} days'}
        return {'key_valid': False, 'msg':f'API Key expired: {expiration_timestamp} {current_timestamp}'}
        
    def list_api_keys(self):
        pattern = self.build_key(KEY_TYPE_API_KEY, '*')
        cursor, keys = self.r.scan(match=pattern)
        for key in keys:
            print(key)
            key_data = self.r.hgetall(key)
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
