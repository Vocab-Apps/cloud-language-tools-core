import os
import argparse
import redis
import redisdb
import string
import random

import cloudlanguagetools.constants

def password_generator():

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


def main():
    r = redisdb.get_redis_connection()

    parser = argparse.ArgumentParser(description='Interact with Redis DB')
    parser.add_argument('--action', choices=['add_key', 'list_api_keys'], help='Indicate what to do', required=True)

    args = parser.parse_args()
    
    if args.action == 'add_key':
        api_key = password_generator()
        redisdb.add_api_key(r, api_key, 'test_key', 'luc')
    elif args.action == 'list_api_keys':
        redisdb.list_api_keys(r)


if __name__ == '__main__':
    main()