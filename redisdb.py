import os
import time
import datetime
import redis
import string
import random
import logging

ENV_VAR_REDIS_URL = 'REDIS_URL'

KEY_TYPE_API_KEY = 'api_key'
KEY_TYPE_PATREON_USER ='patreon_user'

class RedisDb():
    def __init__(self):
        self.connect()

    def connect(self, db_num=0):
        redis_url = os.environ[ENV_VAR_REDIS_URL]

        self.r = redis.from_url(redis_url, db=db_num)

    def build_key(self, key_type, key):
        return f'clt:{key_type}:{key}'

    def get_api_key_expiration_timestamp(self):
        expiration_date = datetime.datetime.now() + datetime.timedelta(days=31)
        key_expiration_timestamp = int(expiration_date.timestamp())
        return key_expiration_timestamp

    def get_api_key_removal_timestamp_millis(self):
        key_removal_date = datetime.datetime.now() + datetime.timedelta(days=61)
        key_removal_timestamp_millis = int(key_removal_date.timestamp() * 1000.0)
        return key_removal_timestamp_millis

    def add_patreon_api_key(self, api_key, user_id, email):
        redis_key = self.build_key(KEY_TYPE_API_KEY, api_key)
        hash_value = {
            'user_id': user_id,
            'email': email,
            'expiration': self.get_api_key_expiration_timestamp(),
            'type': 'patreon'
        }
        self.r.hset(redis_key, mapping=hash_value)
        self.r.expireat(redis_key, self.get_api_key_removal_timestamp_millis())
        logging.info(f'added {redis_key}: {hash_value}, (key removal time: {self.get_api_key_removal_timestamp_millis()})')

        # now add a map from user id to key
        
    def get_patreon_user_key(self, user_id, email):
        logging.info(f'patreon user: {user_id}, email: {email}')
        removal_time_millis = self.get_api_key_removal_timestamp_millis()

        redis_patreon_user_key = self.build_key(KEY_TYPE_PATREON_USER, user_id)
        if self.r.exists(redis_patreon_user_key):
            logging.info(f'mapping exists: patreon user: {user_id}, email: {email} mapping: {redis_patreon_user_key}')
            
            # user already requested a key
            # update expiry time of the key mapping
            logging.info(f'refreshing expiry of mapping: patreon user: {user_id}, email: {email} updating key removal time ({redis_patreon_user_key} / {removal_time_millis})')
            self.r.expireat(redis_patreon_user_key, self.get_api_key_removal_timestamp_millis())

            api_key = self.r.get(redis_patreon_user_key).decode('utf-8')
            redis_api_key = self.build_key(KEY_TYPE_API_KEY, api_key)
            if self.r.exists(redis_api_key):
                # update expiry time
                logging.info(f'refreshing expiry of api key: patreon user: {user_id}, email: {email} updating key removal time ({redis_api_key} / {removal_time_millis})')
                self.r.expireat(redis_api_key, removal_time_millis)
            else:
                # add the key back in
                self.add_patreon_api_key(api_key, user_id, email)
            return api_key
        
        # need to create a new key
        api_key = self.password_generator()
        self.add_patreon_api_key(api_key, user_id, email)

        # map to the patreon user
        self.r.set(redis_patreon_user_key, api_key)
        self.r.expireat(redis_patreon_user_key,removal_time_millis)
        logging.info(f'added mapping: patreon user: {user_id}, email: {email} ({redis_patreon_user_key} / {removal_time_millis})')

        return api_key

    def password_generator(self):

        LETTERS = string.ascii_letters
        NUMBERS = string.digits  
        
        # create alphanumerical from string constants
        printable = f'{LETTERS}{NUMBERS}'

        # convert printable from string to list and shuffle
        printable = list(printable)
        random.shuffle(printable)

        # generate random password and convert to string
        random_password = random.choices(printable, k=16)
        random_password = ''.join(random_password)
        return random_password

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
        return {'key_valid': False, 'msg':f'API Key expired'}
        
    def list_api_keys(self):
        pattern = self.build_key(KEY_TYPE_API_KEY, '*')
        cursor, keys = self.r.scan(match=pattern)
        for key in keys:
            key_str = key.decode('utf-8')
            api_key = key_str.split(':')[-1]
            validity = self.api_key_valid(api_key)
            # print(key)
            key_data = self.r.hgetall(key)
            print(f'{api_key} {key_data}, {validity}')

    def list_all_keys(self):
        cursor, keys = self.r.scan()
        for key in keys:
            key_ttl = self.r.ttl(key)
            expire_time = datetime.datetime.fromtimestamp(float(key_ttl) / 1000.0)
            expire_distance = expire_time - datetime.datetime.now()
            print(f'key: [{key}] expire in: {expire_distance.days} days ({key_ttl})')

    def clear_db(self, wait=True):
        if wait:
            print('WARNING! going to remove all keys after 30s')
            time.sleep(15)
            print('WARNING! going to remove all keys after 15s')
            time.sleep(15)
        self.r.flushdb()
