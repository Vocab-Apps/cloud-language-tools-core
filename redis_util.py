import os
import argparse
import redis
import redisdb
import string
import random
import datetime
import logging

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
    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                        datefmt='%Y%m%d-%H:%M:%S',
                        level=logging.INFO)

    parser = argparse.ArgumentParser(description='Interact with Redis DB')
    choices = ['add_api_key', 'list_api_keys', 'api_key_valid', 'list_all_keys', 'clear_db', 'list_usage']
    parser.add_argument('--action', choices=choices, help='Indicate what to do', required=True)
    parser.add_argument('--api_key', help='Pass in API key to check validity')
    parser.add_argument('--dbnum', help='connect to a different db number', type=int)


    args = parser.parse_args()
    
    connection = redisdb.RedisDb()

    if args.dbnum != None:
        connection.connect(db_num=args.dbnum)

    if args.action == 'add_api_key':
        api_key = password_generator()
        api_key_validity = 30
        connection.add_test_api_key(api_key, datetime.datetime.now() + datetime.timedelta(days=api_key_validity))
    elif args.action == 'list_api_keys':
        connection.list_api_keys()
    elif args.action == 'api_key_valid':
        api_key = args.api_key
        result = connection.api_key_valid(api_key)
        print(result)
    elif args.action == 'list_all_keys':
        connection.list_all_keys()
    elif args.action == 'list_usage':
        connection.list_usage()
    elif args.action == 'clear_db':
        connection.clear_db()


if __name__ == '__main__':
    main()