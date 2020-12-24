import os
import argparse
import redis
import redisdb
import string
import random
import datetime

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
    parser = argparse.ArgumentParser(description='Interact with Redis DB')
    choices = ['add_api_key', 'list_api_keys', 'api_key_valid', 'list_all_keys', 'clear_db']
    parser.add_argument('--action', choices=choices, help='Indicate what to do', required=True)
    parser.add_argument('--api_key', help='Pass in API key to check validity')

    args = parser.parse_args()
    
    connection = redisdb.RedisDb()

    if args.action == 'add_api_key':
        api_key = password_generator()
        connection.add_api_key(api_key, 'test_key', 'luc', datetime.datetime.now() + datetime.timedelta(days=2))
    elif args.action == 'list_api_keys':
        connection.list_api_keys()
    elif args.action == 'api_key_valid':
        api_key = args.api_key
        result = connection.api_key_valid(api_key)
        print(result)
    elif args.action == 'list_all_keys':
        connection.list_all_keys()
    elif args.action == 'clear_db':
        connection.clear_db()


if __name__ == '__main__':
    main()