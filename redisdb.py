import os
import redis

ENV_VAR_REDIS_HOST = 'REDIS_HOST'
ENV_VAR_REDIS_PORT = 'REDIS_PORT'
ENV_VAR_REDIS_PASSWORD ='REDIS_PASSWORD'


def get_redis_connection():
    redis_host = os.environ[ENV_VAR_REDIS_HOST]
    redis_port = os.environ[ENV_VAR_REDIS_PORT]
    redis_password = os.environ[ENV_VAR_REDIS_PASSWORD]

    r = redis.Redis(host=redis_host, port=redis_port, db=0, password=redis_password)
    return r

def add_api_key(r, api_key, key_type, owner):
    redis_key = f'api_key:{api_key}'
    hash_value = {
        'key_type': key_type,
        'owner': owner
    }
    r.hmset(redis_key, hash_value)

def list_api_keys(r):
    cursor, keys = r.scan(match='api_key:*')
    for key in keys:
        print(key)
        key_data = r.hgetall(key)
        print(key_data)

def list_all_keys(r):
    cursor, keys = r.scan()
    for key in keys:
        print(key)