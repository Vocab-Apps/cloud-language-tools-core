import argparse
import redisdb
import convertkit
import logging
import pprint
import pandas

import cloudlanguagetools.constants

def build_trial_user_list(convertkit_client, redis_connection):
    subscribers = convertkit_client.list_subscribers()
    api_key_list = []
    users = []
    for subscriber in subscribers:
        api_key = subscriber['fields']['trial_api_key']
        email = subscriber['email_address']
        users.append({
            'api_key': api_key,
            'email': email
        })
        api_key_list.append(api_key)
    users_df = pandas.DataFrame(users)
    api_key_usage = redis_connection.get_trial_user_usage(api_key_list)
    api_key_usage_df = pandas.DataFrame(api_key_usage)

    combined_df = pandas.merge(users_df, api_key_usage_df, how='left', on='api_key')
    print(combined_df)
    
    return
    pprint.pprint(subscribers)
    for subscriber in subscribers:
        subscriber_id = subscriber['id']
        tag_list = convertkit_client.list_tags(subscriber_id)
        print(tag_list)

def main():
    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                        datefmt='%Y%m%d-%H:%M:%S',
                        level=logging.INFO)

    parser = argparse.ArgumentParser(description='Utilities to manager trial users')
    choices = ['list_trial_users']
    parser.add_argument('--action', choices=choices, help='Indicate what to do', required=True)
    parser.add_argument('--trial_email', help='email address of trial user')


    args = parser.parse_args()
    
    redis_connection = redisdb.RedisDb()
    convertkit_client = convertkit.ConvertKit()

    if args.action == 'list_trial_users':
        build_trial_user_list(convertkit_client, redis_connection)
    else:
        print(f'not recognized: {args.action}')


if __name__ == '__main__':
    main()