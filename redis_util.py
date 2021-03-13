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
    choices = ['add_api_key', 
               'list_api_keys', 
               'api_key_valid', 
               'list_all_keys', 
               'clear_db', 
               'list_usage', 
               'create_trial_key', 
               'increase_trial_limit']
    parser.add_argument('--action', choices=choices, help='Indicate what to do', required=True)
    parser.add_argument('--api_key', help='Pass in API key to check validity')
    parser.add_argument('--trial_email', help='email address of trial user')
    parser.add_argument('--pattern', help='Use a special pattern for key iteration')
    parser.add_argument('--dbnum', help='connect to a different db number', type=int)


    args = parser.parse_args()
    
    connection = redisdb.RedisDb()

    if args.dbnum != None:
        connection.connect(db_num=args.dbnum)

    if args.action == 'add_api_key':
        api_key = password_generator()
        connection.add_test_api_key(api_key)
    elif args.action == 'list_api_keys':
        connection.list_api_keys()
    elif args.action == 'api_key_valid':
        api_key = args.api_key
        connection.show_key_data(api_key)
        result = connection.api_key_valid(api_key)
        print(result)
    elif args.action == 'list_all_keys':
        connection.list_all_keys()
    elif args.action == 'list_usage':
        # example: python redis_util.py --action list_usage --pattern usage:global:daily
        connection.list_usage(args.pattern)
    elif args.action == 'create_trial_key':
        email = args.trial_email
        connection.get_trial_user_key(email)
    elif args.action == 'increase_trial_limit':
        email = args.trial_email
        connection.increase_trial_key_limit(email, 100000)
    elif args.action == 'clear_db':
        connection.clear_db()
    else:
        print(f'not recognized: {args.action}')


if __name__ == '__main__':
    main()