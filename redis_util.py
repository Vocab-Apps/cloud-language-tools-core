import os
import argparse
import redis
import redisdb
import cloudlanguagetools.constants


def main():

    r = redisdb.get_redis_connection()

    # r.set('test_key', 'test1')
    # print(r.get('test_key'))
    r.delete('test_key')


if __name__ == '__main__':
    main()