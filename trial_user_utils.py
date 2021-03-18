import argparse
import redisdb
import convertkit
import quotas
import logging
import pprint
import pandas
import datetime

import cloudlanguagetools.constants

def build_trial_user_list(convertkit_client, redis_connection):
    subscribers = convertkit_client.list_subscribers()
    api_key_list = []
    users = []
    for subscriber in subscribers:
        # print(subscriber)
        api_key = subscriber['fields']['trial_api_key']
        email = subscriber['email_address']
        users.append({
            'subscribe_time': subscriber['created_at'],
            'subscriber_id': subscriber['id'],
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
    combined_df['character_limit'] = combined_df['character_limit'].astype(int)
    combined_df['subscribe_time'] = combined_df['subscribe_time'].astype('datetime64')

    # combined_df = combined_df.sort_values(by='characters', ascending=False).reset_index()

    return combined_df

def get_upgrade_eligible_users(convertkit_client, redis_connection):
    user_list_df = build_trial_user_list(convertkit_client, redis_connection)

    eligible_users = user_list_df[(user_list_df['character_limit'] == quotas.TRIAL_USER_CHARACTER_LIMIT) & (user_list_df['characters'] > (quotas.TRIAL_USER_CHARACTER_LIMIT - 300))]

    return eligible_users

def get_inactive_users(convertkit_client, redis_connection):
    user_list_df = build_trial_user_list(convertkit_client, redis_connection)

    cutoff_time = datetime.datetime.now() - datetime.timedelta(days=3)
    inactive_users = user_list_df[(user_list_df['characters'] == 0) & (user_list_df['subscribe_time'] < cutoff_time)]

    subscriber_id_list = list(inactive_users['subscriber_id'])
    tag_entries = []
    for subscriber_id in subscriber_id_list:
        tag_list = convertkit_client.list_tags(subscriber_id)
        for tag_entry in tag_list:
            tag_entry['subscriber_id'] = subscriber_id
            tag_entries.append(tag_entry)
    tag_entries_df = pandas.DataFrame(tag_entries)

    tag_entries_inactive_df = tag_entries_df[tag_entries_df['id'] == convertkit_client.tag_id_trial_inactive]
    tag_entries_inactive_df = tag_entries_inactive_df.rename(columns={'id': 'tag_id', 'name': 'tag_name'})
    tag_entries_inactive_df['tagged_inactive'] = True
    tag_entries_inactive_df = tag_entries_inactive_df[['subscriber_id', 'tagged_inactive']]

    combined_df = pandas.merge(inactive_users, tag_entries_inactive_df, how='left', on='subscriber_id')
    combined_df['tagged_inactive'] = combined_df['tagged_inactive'].fillna(False)

    return combined_df

def perform_upgrade_eligible_users(convertkit_client, redis_connection):
    eligible_users_df = get_upgrade_eligible_users(convertkit_client, redis_connection)

    for index, row in eligible_users_df.iterrows():
        email = row['email']
        logging.info(f'eligible user: {email}')

        # increase API key character limit
        redis_connection.increase_trial_key_limit(email, quotas.TRIAL_EXTENDED_USER_CHARACTER_LIMIT)
        # tag user on convertkit
        convertkit_client.tag_user_trial_extended(email)

def process_inactive_users(convertkit_client, redis_connection):
    inactive_users = get_inactive_users(convertkit_client, redis_connection)

    not_tagged_df = inactive_users[inactive_users['tagged_inactive'] == False]
    for index, row in not_tagged_df.iterrows():
        email = row['email']
        logging.info(f'tagging {email} inactive')
        convertkit_client.tag_user_trial_inactive(email)

    logging.info('done processing inactive users')

def main():
    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                        datefmt='%Y%m%d-%H:%M:%S',
                        level=logging.INFO)

    parser = argparse.ArgumentParser(description='Utilities to manager trial users')
    choices = ['list_trial_users', 
    'list_eligible_upgrade_users', 
    'perform_eligible_upgrade_users', 
    'list_inactive_users',
    'process_inactive_users'
    ]
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
    elif args.action == 'list_inactive_users':
        inactive_df = get_inactive_users(convertkit_client, redis_connection)
        print(inactive_df)
    elif args.action == 'perform_eligible_upgrade_users':
        perform_upgrade_eligible_users(convertkit_client, redis_connection)
    elif args.action == 'process_inactive_users':
        process_inactive_users(convertkit_client, redis_connection)
    else:
        print(f'not recognized: {args.action}')


if __name__ == '__main__':
    main()