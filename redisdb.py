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