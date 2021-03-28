import argparse
import redisdb
import convertkit
import quotas
import logging
import pprint
import pandas
import datetime
import os
import requests


import cloudlanguagetools.constants

class TrialUserUtils():
    def __init__(self):
        self.redis_connection = redisdb.RedisDb()
        self.convertkit_client = convertkit.ConvertKit()

        self.airtable_api_key = os.environ['AIRTABLE_API_KEY']
        self.airtable_trial_users_url = os.environ['AIRTABLE_TRIAL_USERS_URL']

    def get_dataframe_from_subscriber_list(self, subscribers):
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
        users_df = pandas.DataFrame(users)
        return users_df

    def get_dataframe_for_tag(self, tag_id, tag_name, tag_column):
        subscribers = self.convertkit_client.list_subscribers_tag(tag_id)
        data_df = self.get_dataframe_from_subscriber_list(subscribers)
        data_df[tag_column] = tag_name
        data_df = data_df[['subscriber_id', tag_column]]
        return data_df

    def build_trial_user_list(self):
        subscribers = self.convertkit_client.list_trial_users()

    
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

        subscribers_trial_extended = self.get_dataframe_for_tag(self.convertkit_client.tag_id_trial_extended, 'trial_extended', 'tag_1')
        subscribers_trial_inactive = self.get_dataframe_for_tag(self.convertkit_client.tag_id_trial_inactive, 'trial_user_inactive', 'tag_2')
        subscribers_trial_end = self.get_dataframe_for_tag(self.convertkit_client.tag_id_trial_end_reach_out, 'trial_end_reach_out', 'tag_3')
        combined_df = pandas.merge(users_df, subscribers_trial_extended, how='left', on='subscriber_id')
        combined_df = pandas.merge(combined_df, subscribers_trial_inactive, how='left', on='subscriber_id')
        combined_df = pandas.merge(combined_df, subscribers_trial_end, how='left', on='subscriber_id')
        combined_df = combined_df.fillna('')
        # print(combined_df)

        # get character entitlement
        entitlement = self.redis_connection.get_trial_user_entitlement(api_key_list)
        entitlement_df = pandas.DataFrame(entitlement)
        # get usage
        api_key_usage = self.redis_connection.get_trial_user_usage(api_key_list)
        api_key_usage_df = pandas.DataFrame(api_key_usage)

        combined_df = pandas.merge(combined_df, api_key_usage_df, how='left', on='api_key')
        combined_df = pandas.merge(combined_df, entitlement_df, how='left', on='api_key')

        combined_df = combined_df.fillna(0)

        combined_df['characters'] =  combined_df['characters'].astype(int)
        combined_df['character_limit'] = combined_df['character_limit'].astype(int)
        combined_df['subscribe_time'] = combined_df['subscribe_time'].astype('datetime64')

        # combined_df = combined_df.sort_values(by='characters', ascending=False).reset_index()

        return combined_df

    def get_inactive_users(self):
        user_list_df = self.build_trial_user_list()

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

    def get_upgrade_users_inactive(self):
        # users who didn't take advantage of their upgraded quota

        user_list_df = self.build_trial_user_list()
        subset = user_list_df[(user_list_df['characters'] < quotas.TRIAL_USER_CHARACTER_LIMIT) & (user_list_df['character_limit'] == quotas.TRIAL_EXTENDED_USER_CHARACTER_LIMIT)]

        print(subset)


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

    def update_trial_users_airtable(self):
        user_list_df = self.build_trial_user_list()
        # print(user_list_df)

        # first, list records
        response = requests.get(self.airtable_trial_users_url, headers={'Authorization': f'Bearer {self.airtable_api_key}'})
        data = response.json()
        airtable_records = []
        for record in data['records']:
            airtable_records.append({'id': record['id'], 'email': record['fields']['email']})
        airtable_records_df = pandas.DataFrame(airtable_records)

        combined_df = pandas.merge(airtable_records_df, user_list_df, how='inner', on='email')

        records = combined_df.to_dict(orient='records')

        # print(records)

        update_instructions = [
            {'id': x['id'], 
            'fields': 
                {
                    'characters': x['characters'], 
                    'character_limit': x['character_limit'],
                    'trial_api_key': x['api_key'],
                    'tags': [x for x in [x['tag_1'], x['tag_2'], x['tag_3']] if x != '']
                }
            } for x in records]
        # pprint.pprint(update_instructions)

        headers = {
            'Authorization': f'Bearer {self.airtable_api_key}',
            'Content-Type': 'application/json' }
        while len(update_instructions) > 0:
            slice_length = min(10, len(update_instructions))
            update_slice = update_instructions[0:slice_length]
            del update_instructions[0:slice_length]
            
            # pprint.pprint(update_slice)
            logging.info(f'updating records')
            response = requests.patch(self.airtable_trial_users_url, json={
                'records': update_slice
            }, headers=headers)
            if response.status_code != 200:
                logging.error(response.content)
            # logging.info(f'response.status_code: {response.status_code}')


    def perform_airtable_tag_requests(self):
        pass


def main():
    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                        datefmt='%Y%m%d-%H:%M:%S',
                        level=logging.INFO)

    parser = argparse.ArgumentParser(description='Utilities to manager trial users')
    choices = ['list_trial_users', 
    'list_eligible_upgrade_users', 
    'perform_eligible_upgrade_users', 
    'list_inactive_users',
    'process_inactive_users',
    'list_upgrade_users_inactive',
    'list_extended_users_maxed_out',
    'update_trial_users_airtable'
    ]
    parser.add_argument('--action', choices=choices, help='Indicate what to do', required=True)
    parser.add_argument('--trial_email', help='email address of trial user')


    args = parser.parse_args()
    
    trial_users_utils = TrialUserUtils()

    if args.action == 'list_trial_users':
        user_list_df = trial_users_utils.build_trial_user_list()
        print(user_list_df.tail(50))
    elif args.action == 'list_eligible_upgrade_users':
        eligible_df = trial_users_utils.get_upgrade_eligible_users()
        print(eligible_df)
    elif args.action == 'list_inactive_users':
        inactive_df = trial_users_utils.get_inactive_users()
        print(inactive_df)
    elif args.action == 'perform_eligible_upgrade_users':
        trial_users_utils.perform_upgrade_eligible_users()
    elif args.action == 'process_inactive_users':
        trial_users_utils.process_inactive_users()
    elif args.action == 'list_upgrade_users_inactive':
        trial_users_utils.get_upgrade_users_inactive()
    elif args.action == 'list_extended_users_maxed_out':
        users_df = trial_users_utils.get_extended_users_maxed_out()
        print(users_df)
    elif args.action == 'update_trial_users_airtable':
        trial_users_utils.update_trial_users_airtable()
    else:
        print(f'not recognized: {args.action}')


if __name__ == '__main__':
    main()