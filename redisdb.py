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
KEY_TYPE_USAGE ='usage'

KEY_PREFIX = 'clt'

class RedisDb():
    def __init__(self):
        self.connect()

    def connect(self, db_num=0):
        redis_url = os.environ[ENV_VAR_REDIS_URL]
        logging.info(f'connecting to redis url: {redis_url}, db_num: {db_num}')

        self.r = redis.from_url(redis_url, db=db_num, decode_responses=True)

    def build_key(self, key_type, key):
        return f'{KEY_PREFIX}:{key_type}:{key}'

    def get_api_key_expiration_timestamp(self):
        expiration_date = datetime.datetime.now() + datetime.timedelta(days=60)
        key_expiration_timestamp = int(expiration_date.timestamp())
        return key_expiration_timestamp

    def add_test_api_key(self, api_key, expiration_datetime):
        redis_key = self.build_key(KEY_TYPE_API_KEY, api_key)
        hash_value = {
            'expiration': int(expiration_datetime.timestamp()),
            'type': 'test'
        }
        self.r.hset(redis_key, mapping=hash_value)
        logging.info(f'added {redis_key}: {hash_value}')

    def add_patreon_api_key(self, api_key, user_id, email):
        redis_key = self.build_key(KEY_TYPE_API_KEY, api_key)
        hash_value = {
            'user_id': user_id,
            'email': email,
            'expiration': self.get_api_key_expiration_timestamp(),
            'type': 'patreon'
        }
        self.r.hset(redis_key, mapping=hash_value)
        logging.info(f'added {redis_key}: {hash_value}')
        
    def get_patreon_user_key(self, user_id, email):
        logging.info(f'patreon user: {user_id}, email: {email}')

        redis_patreon_user_key = self.build_key(KEY_TYPE_PATREON_USER, user_id)
        if self.r.exists(redis_patreon_user_key):
            logging.info(f'mapping exists: patreon user: {user_id}, email: {email} mapping: {redis_patreon_user_key}')
            
            # user already requested a key
            api_key = self.r.get(redis_patreon_user_key)
            redis_api_key = self.build_key(KEY_TYPE_API_KEY, api_key)
            if self.r.exists(redis_api_key):
                # update expiry time
                expiration_timestamp = self.get_api_key_expiration_timestamp()
                logging.info(f'refreshing expiration date of api key: patreon user: {user_id}, email: {email} updating key removal time ({redis_api_key} / {expiration_timestamp})')
                self.r.hset(redis_api_key, 'expiration', expiration_timestamp)
            else:
                # add the key back in
                self.add_patreon_api_key(api_key, user_id, email)
            return api_key
        
        # need to create a new key
        api_key = self.password_generator()
        self.add_patreon_api_key(api_key, user_id, email)

        # map to the patreon user
        self.r.set(redis_patreon_user_key, api_key)
        logging.info(f'added mapping: patreon user: {user_id}, email: {email} ({redis_patreon_user_key})')

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
        result = []
        pattern = self.build_key(KEY_TYPE_API_KEY, '*')
        cursor, keys = self.r.scan(match=pattern)
        for key in keys:
            key_str = key
            api_key = key_str.split(':')[-1]
            validity = self.api_key_valid(api_key)
            # print(key)
            key_data = self.r.hgetall(key)
            result.append({
                'api_key': api_key,
                'key_data': key_data,
                'validity': validity
            })
            print(f'{api_key} {key_data}, {validity}')
        return result

    def list_all_keys(self):
        cursor, keys = self.r.scan()
        for key in keys:
            key_ttl = self.r.ttl(key)
            expiration = 'permanent'
            if key_ttl != -1:
                expire_distance = datetime.timedelta(seconds=key_ttl)
                expiration = f'expire: {expire_distance.days} days ({expire_distance.seconds} seconds)'
            print(f'key: [{key}] ({expiration})')

    def track_usage(self, api_key, service, request_type, characters):
        yyyymmdd_date_str = datetime.datetime.today().strftime('%Y%m%d')
        yyyymm_date_str = datetime.datetime.today().strftime('%Y%m')
        expire_time_seconds = 30*3*24*3600 # 3 months
        
        key_list = [
            self.build_key(KEY_TYPE_USAGE + ':user:daily', f'{yyyymmdd_date_str}:{service}:{request_type}:{api_key}'),
            self.build_key(KEY_TYPE_USAGE + ':user:monthly', f'{yyyymm_date_str}:{service}:{request_type}:{api_key}'),
            self.build_key(KEY_TYPE_USAGE + ':global:daily', f'{yyyymmdd_date_str}:{service}:{request_type}'),
            self.build_key(KEY_TYPE_USAGE + ':global:monthly', f'{yyyymm_date_str}:{service}:{request_type}')
        ]

        for key in key_list:
            self.r.hincrby(key, 'characters', characters)
            self.r.hincrby(key, 'requests', 1)
            self.r.expire(key, expire_time_seconds)

    def list_usage(self):
        pattern = self.build_key(KEY_TYPE_USAGE, '*')
        for key in self.r.scan_iter(pattern):
            value = self.r.hgetall(key)
            print(f'{key}: {value}')

    def clear_db(self, wait=True):
        if wait:
            print('WARNING! going to remove all keys after 30s')
            time.sleep(15)
            print('WARNING! going to remove all keys after 15s')
            time.sleep(15)
        self.r.flushdb()
