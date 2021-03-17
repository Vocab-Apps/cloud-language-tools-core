import argparse
import redisdb
import convertkit
import quotas
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
    
    # get character entitlement
    entitlement = redis_connection.get_trial_user_entitlement(api_key_list)
    entitlement_df = pandas.DataFrame(entitlement)
    # get usage
    api_key_usage = redis_connection.get_trial_user_usage(api_key_list)
    api_key_usage_df = pandas.DataFrame(api_key_usage)

    combined_df = pandas.merge(users_df, api_key_usage_df, how='left', on='api_key')
    combined_df = pandas.merge(combined_df, entitlement_df, how='left', on='api_key')

    combined_df = combined_df.fillna(0)

    combined_df['characters'] =  combined_df['characters'].astype(int)
    combined_df['character_limit'] =  combined_df['character_limit'].astype(int)

    return combined_df

def get_upgrade_eligible_users(convertkit_client, redis_connection):
    user_list_df = build_trial_user_list(convertkit_client, redis_connection)

    eligible_users = user_list_df[(user_list_df['character_limit'] == quotas.TRIAL_USER_CHARACTER_LIMIT) & (user_list_df['characters'] > (quotas.TRIAL_USER_CHARACTER_LIMIT - 300))]

    print(eligible_users)

def main():
    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                        datefmt='%Y%m%d-%H:%M:%S',
                        level=logging.INFO)

    parser = argparse.ArgumentParser(description='Utilities to manager trial users')
    choices = ['list_trial_users', 'list_eligible_upgrade_users']
    parser.add_argument('--action', choices=choices, help='Indicate what to do', required=True)
    parser.add_argument('--trial_email', help='email address of trial user')


    args = parser.parse_args()
    
    redis_connection = redisdb.RedisDb()
    convertkit_client = convertkit.ConvertKit()

    if args.action == 'list_trial_users':
        user_list_df = build_trial_user_list(convertkit_client, redis_connection)
        print(user_list_df)
    elif args.action == 'list_eligible_upgrade_users':
        eligible_df = get_upgrade_eligible_users(convertkit_client, redis_connection)
        print(eligible_df)
    else:
        print(f'not recognized: {args.action}')


if __name__ == '__main__':
    main()