import os
import time
import datetime
import redis
import json
import string
import random
import logging
import cloudlanguagetools.constants
import cloudlanguagetools.errors
import quotas

ENV_VAR_REDIS_URL = 'REDIS_URL'

KEY_TYPE_API_KEY = 'api_key'
KEY_TYPE_PATREON_USER ='patreon_user'
KEY_TYPE_TRIAL_USER = 'trial_user'
KEY_TYPE_USAGE ='usage'
KEY_TYPE_USER_CLIENT ='user_client'
KEY_TYPE_USER_CLIENT_VERSION ='user_client_version'
KEY_TYPE_USER_REQUEST_MODE ='user_request_mode'
KEY_TYPE_USER_SERVICE ='user_service'
KEY_TYPE_USER_AUDIO_LANGUAGE ='user_audio_language'
KEY_TYPE_AUDIO_LOG ='audio_log'

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

    def build_monthly_user_key(self, key_type, api_key):
        date_str = datetime.datetime.today().strftime('%Y%m')
        redis_key = self.build_key(key_type, f'{date_str}:{api_key}')
        return redis_key

    def get_specific_api_key_expiration_timestamp(self, delta_days):
        expiration_date = datetime.datetime.now() + datetime.timedelta(days=delta_days)
        key_expiration_timestamp = int(expiration_date.timestamp())
        return key_expiration_timestamp    

    def get_api_key_expiration_timestamp(self):
        expiration_date = datetime.datetime.now() + datetime.timedelta(days=60)
        key_expiration_timestamp = int(expiration_date.timestamp())
        return key_expiration_timestamp

    def add_test_api_key(self, api_key):
        redis_key = self.build_key(KEY_TYPE_API_KEY, api_key)
        hash_value = {
            'expiration': self.get_api_key_expiration_timestamp(),
            'type': cloudlanguagetools.constants.ApiKeyType.test.name
        }
        self.r.hset(redis_key, mapping=hash_value)
        logging.info(f'added {redis_key}: {hash_value}')

    # prod workflow (app.py/patreon_key)
    def add_patreon_api_key(self, api_key, user_id, email):
        redis_key = self.build_key(KEY_TYPE_API_KEY, api_key)
        hash_value = {
            'user_id': user_id,
            'email': email,
            'expiration': self.get_api_key_expiration_timestamp(),
            'type': cloudlanguagetools.constants.ApiKeyType.patreon.name
        }
        self.r.hset(redis_key, mapping=hash_value)
        logging.info(f'added {redis_key}: {hash_value}')

    def add_trial_api_key(self, api_key, email, character_limit):
        redis_key = self.build_key(KEY_TYPE_API_KEY, api_key)
        hash_value = {
            'email': email,
            'expiration': self.get_api_key_expiration_timestamp(),
            'type': cloudlanguagetools.constants.ApiKeyType.trial.name,
            'character_limit': character_limit
        }
        self.r.hset(redis_key, mapping=hash_value)
        logging.info(f'added {redis_key}: {hash_value}')        
        
    # prod workflow
    def get_trial_user_key(self, email):
        redis_trial_user_key = self.build_key(KEY_TYPE_TRIAL_USER, email)
        if self.r.exists(redis_trial_user_key):
            # user already requested a key
            api_key = self.r.get(redis_trial_user_key)
            redis_api_key = self.build_key(KEY_TYPE_API_KEY, api_key)
            if not self.r.exists(redis_api_key):
                # add the key back in
                self.add_trial_api_key(api_key, email, quotas.TRIAL_USER_CHARACTER_LIMIT)
            return api_key
        
        # need to create a new key
        api_key = self.password_generator()
        self.add_trial_api_key(api_key, email, quotas.TRIAL_USER_CHARACTER_LIMIT)

        # map to the patreon user
        self.r.set(redis_trial_user_key, api_key)
        logging.info(f'added mapping: trial user: email: {email} ({redis_trial_user_key})')

        return api_key
    
    def increase_trial_key_limit(self, email, character_limit):
        redis_trial_user_key = self.build_key(KEY_TYPE_TRIAL_USER, email)
        if self.r.exists(redis_trial_user_key):
            api_key = self.r.get(redis_trial_user_key)
            redis_api_key = self.build_key(KEY_TYPE_API_KEY, api_key)

            # set character limit
            self.r.hset(redis_api_key, 'character_limit', character_limit)

            logging.info(f'increased character limit to {character_limit} for {email} {api_key}')


    # prod workflow (app.py/patreon_key)
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

    def show_key_data(self, api_key):
        redis_key = self.build_key(KEY_TYPE_API_KEY, api_key)
        key_data = self.r.hgetall(redis_key)
        logging.info(key_data)

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
        redis_api_key_list = []

        logging.info('scanning list of API keys from redis')
        cursor = '0'
        while cursor != 0:
            cursor, keys = self.r.scan(cursor=cursor, match=pattern, count=100)
            for key in keys:
                redis_api_key_list.append(key)

        # get key data for all keys
        logging.info('getting data for all API keys')
        pipe = self.r.pipeline()
        for redis_api_key in redis_api_key_list:
            pipe.hgetall(redis_api_key)
        hashes = pipe.execute()
        for redis_api_key, value in zip(redis_api_key_list, hashes):
            api_key = redis_api_key.split(':')[-1]
            result.append({
                'api_key': api_key,
                'key_data': value
            })

        return result

    def list_all_keys(self):
        for key in self.r.scan_iter(count=100):
            print(f'key: [{key}]')
            # key_ttl = self.r.ttl(key)
            # expiration = 'permanent'
            # if key_ttl != -1:
            #     # note: the digital ocean redis DB seems to return a ttl in number of seconds
            #     expire_distance = datetime.timedelta(seconds=key_ttl)
            #     expiration = f'expire: {expire_distance.days} days ({expire_distance.seconds} seconds) [ttl: {key_ttl}]' 
            # print(f'key: [{key}] ({expiration})')

    # default expire time for usage-style keys
    def get_expire_time_usage(self):
        expire_time_seconds = 30*3*24*3600 # 3 months
        return expire_time_seconds

    def log_audio_request(self, api_key, data):
        date_str = datetime.datetime.today().strftime('%Y%m')
        redis_key = self.build_key(KEY_TYPE_AUDIO_LOG, date_str)
        data['api_key'] = api_key
        value_str = json.dumps(data)
        self.r.rpush(redis_key, value_str)
        self.r.expire(redis_key, self.get_expire_time_usage())

    def track_audio_language(self, api_key, language_code):
        redis_key = self.build_monthly_user_key(KEY_TYPE_USER_AUDIO_LANGUAGE, api_key)
        self.r.hincrby(redis_key, language_code.name, 1)
        self.r.expire(redis_key, self.get_expire_time_usage())

    def track_service(self, api_key, service):
        redis_key = self.build_monthly_user_key(KEY_TYPE_USER_SERVICE, api_key)
        self.r.hincrby(redis_key, service.name, 1)
        self.r.expire(redis_key, self.get_expire_time_usage())        

    def track_client(self, api_key, client_str, version):
        # keep track of the client used
        client = cloudlanguagetools.constants.Client[client_str]
        redis_key = self.build_monthly_user_key(KEY_TYPE_USER_CLIENT, api_key)
        self.r.hincrby(redis_key, client.name, 1)
        self.r.expire(redis_key, self.get_expire_time_usage())
        # keep track of version used
        client_version = f'{client_str}_{version}'
        redis_key = self.build_monthly_user_key(KEY_TYPE_USER_CLIENT_VERSION, api_key)
        self.r.hincrby(redis_key, client_version, 1)
        self.r.expire(redis_key, self.get_expire_time_usage())

    def track_request_mode(self, api_key, request_mode):
        # keep track of the client used
        redis_key = self.build_monthly_user_key(KEY_TYPE_USER_REQUEST_MODE, api_key)
        self.r.hincrby(redis_key, request_mode.name, 1)
        self.r.expire(redis_key, self.get_expire_time_usage())    

    def track_usage(self, api_key, service, request_type, characters: int, language_code=None):
        expire_time_seconds = 30*3*24*3600 # 3 months

        if language_code != None:
            # azure has special character counting based on language
            characters = quotas.adjust_character_count(service, request_type, language_code, characters)

        redis_api_key = self.build_key(KEY_TYPE_API_KEY, api_key)
        key_type_str = self.r.hget(redis_api_key, 'type')
        key_type = cloudlanguagetools.constants.ApiKeyType[key_type_str]
        character_limit_str = self.r.hget(redis_api_key, 'character_limit')
        character_limit = None
        if character_limit_str != None:
            character_limit = int(character_limit_str)
        
        usage_slice_list = [
            quotas.UsageSlice(request_type, 
                              cloudlanguagetools.constants.UsageScope.User, 
                              cloudlanguagetools.constants.UsagePeriod.daily, 
                              service, 
                              api_key,
                              key_type,
                              character_limit),
            quotas.UsageSlice(request_type, 
                              cloudlanguagetools.constants.UsageScope.User, 
                              cloudlanguagetools.constants.UsagePeriod.monthly, 
                              service, 
                              api_key,
                              key_type,
                              character_limit),
            quotas.UsageSlice(request_type, 
                              cloudlanguagetools.constants.UsageScope.User, 
                              cloudlanguagetools.constants.UsagePeriod.lifetime, 
                              service, 
                              api_key,
                              key_type,
                              character_limit),                              
            quotas.UsageSlice(request_type, 
                              cloudlanguagetools.constants.UsageScope.Global, 
                              cloudlanguagetools.constants.UsagePeriod.daily, 
                              service, 
                              api_key,
                              key_type,
                              character_limit),
            quotas.UsageSlice(request_type, 
                              cloudlanguagetools.constants.UsageScope.Global, 
                              cloudlanguagetools.constants.UsagePeriod.monthly, 
                              service, 
                              api_key,
                              key_type,
                              character_limit),
        ]

        def convert_usage(usage_output):
            if usage_output == None:
                return 0
            return int(usage_output)

        # do a pre check to see whether the current request would put us over the quota
        for usage_slice in usage_slice_list:
            key = self.build_key(KEY_TYPE_USAGE, usage_slice.build_key_suffix())
            current_quota_characters = convert_usage(self.r.hget(key, 'characters'))
            current_quota_requests = convert_usage(self.r.hget(key, 'requests'))
            
            if usage_slice.over_quota(current_quota_characters + characters, current_quota_requests + 1):
                error_msg = f'Exceeded {usage_slice.usage_scope.name} {usage_slice.usage_period.name} quota'
                raise cloudlanguagetools.errors.OverQuotaError(error_msg)        

        # track usage
        for usage_slice in usage_slice_list:
            key = self.build_key(KEY_TYPE_USAGE, usage_slice.build_key_suffix())
            self.r.hincrby(key, 'characters', characters)
            self.r.hincrby(key, 'requests', 1)
            self.r.expire(key, expire_time_seconds)

    def list_user_tracking_data(self, api_key_entry_list):

        # process api key list
        api_key_list = [x['api_key'] for x in api_key_entry_list]

        monthly_user_key_types = [
            KEY_TYPE_USER_AUDIO_LANGUAGE,
            KEY_TYPE_USER_SERVICE,
            KEY_TYPE_USER_CLIENT,
            KEY_TYPE_USER_CLIENT_VERSION
        ]

        record_lists = {}

        i = 0
        batch_size = 80
        total_length = len(api_key_list)
        while len(api_key_list) > 0:
            # logging.info(f'requesting batch {i} (total length {total_length})')
            split_len = min(len(api_key_list), batch_size)
            current_batch = api_key_list[:split_len]
            api_key_list = api_key_list[split_len:]

            for key_type in monthly_user_key_types:
                if key_type not in record_lists:
                    record_lists[key_type] = []
                pipe = self.r.pipeline()
                for api_key in current_batch:
                    redis_key = self.build_monthly_user_key(key_type, api_key)
                    pipe.hgetall(redis_key)
                hashes = pipe.execute()
                for key, hash_data in zip(current_batch, hashes):
                    if len(hash_data) > 0:
                        # logging.info(f'key: {key} hash_data: {hash_data}')
                        record_lists[key_type].append({
                            'api_key': key,
                            'data': hash_data
                        })
            i += 1
        
        return record_lists


    def list_usage(self, scan_pattern):
        # first, build list of keys
        if scan_pattern == None:
            pattern = self.build_key(KEY_TYPE_USAGE, '*')
        else:
            pattern = self.build_key(scan_pattern, '*')
        
        key_list = []
        cursor = '0'
        while cursor != 0:
            cursor, keys = self.r.scan(cursor=cursor, match=pattern, count=100)
            key_list.extend(keys)
        pipe = self.r.pipeline()
        for key in key_list:
            pipe.hgetall(key)
        hashes = pipe.execute()
        usage_entries = []
        for key, hash_data in zip(key_list, hashes):
            usage_entry = {
                'usage_key': key
            }
            usage_entry.update(hash_data)
            usage_entries.append(usage_entry)
        return usage_entries
        
    def list_trial_users(self):
        pattern = self.build_key(KEY_TYPE_TRIAL_USER, '*')
        api_key_list = []
        cursor = '0'
        while cursor != 0:
            cursor, keys = self.r.scan(cursor=cursor, match=pattern, count=100)
            pipe = self.r.pipeline()
            for key in keys:
                pipe.get(key)
            key_values = pipe.execute()
            for key, value in zip(keys, key_values):
                api_key_list.append(value)

        # get trial user data
        pipe = self.r.pipeline()
        for api_key in api_key_list:
            redis_api_key = self.build_key(KEY_TYPE_API_KEY, api_key)
            pipe.hgetall(redis_api_key)
        user_data = pipe.execute()

        # get current usage
        pipe = self.r.pipeline()
        for api_key in api_key_list:
            redis_usage = self.build_key(KEY_TYPE_USAGE, f'user:lifetime:{api_key}')
            # print(redis_usage)
            pipe.hgetall(redis_usage)
        usage_data = pipe.execute()

        for api_key, user, usage in zip(api_key_list, user_data, usage_data):
            print(f'{api_key}: {user}, {usage}')

    def get_trial_user_entitlement(self, api_key_list):
        pipe = self.r.pipeline()
        for api_key in api_key_list:
            redis_usage = self.build_key(KEY_TYPE_API_KEY, api_key)
            pipe.hget(redis_usage, 'character_limit')
        usage_data = pipe.execute()
        entries = []
        for api_key, characters in zip(api_key_list, usage_data):
            entries.append({'api_key': api_key, 'character_limit': characters})
        return entries

    def get_trial_user_usage(self, api_key_list):
        pipe = self.r.pipeline()
        for api_key in api_key_list:
            redis_usage = self.build_key(KEY_TYPE_USAGE, f'user:lifetime:{api_key}')
            # print(redis_usage)
            pipe.hget(redis_usage, 'characters')
        usage_data = pipe.execute()
        entries = []
        for api_key, characters in zip(api_key_list, usage_data):
            # print(f'api_key: {api_key} characters: {characters}')
            entries.append({'api_key': api_key, 'characters': characters})
        return entries
    
    def show_hash_key(self, redis_key):
        hash_data = self.r.hgetall(redis_key)
        logging.info(f'{redis_key}: {hash_data}')

    def remove_key(self, redis_key):
        logging.warn(f'WARNING about to remove key: {redis_key}')
        time.sleep(15)
        self.r.delete(redis_key)


    def clear_db(self, wait=True):
        if wait:
            print('WARNING! going to remove all keys after 30s')
            time.sleep(15)
            print('WARNING! going to remove all keys after 15s')
            time.sleep(15)
        self.r.flushdb()
