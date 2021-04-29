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

        self.tag_columns_list = ['tag_1', 'tag_2', 'tag_3', 'tag_4']

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

        subscribers_trial_extended = self.get_dataframe_for_tag(self.convertkit_client.tag_id_trial_extended, 'trial_extended', self.tag_columns_list[0])
        subscribers_trial_inactive = self.get_dataframe_for_tag(self.convertkit_client.tag_id_trial_inactive, 'trial_user_inactive', self.tag_columns_list[1])
        subscribers_trial_end = self.get_dataframe_for_tag(self.convertkit_client.tag_id_trial_end_reach_out, 'trial_end_reach_out', self.tag_columns_list[2])
        subscribers_trial_patreon_convert = self.get_dataframe_for_tag(self.convertkit_client.tag_id_trial_patreon_convert, 'trial_patreon_convert', self.tag_columns_list[3])
        combined_df = pandas.merge(users_df, subscribers_trial_extended, how='left', on='subscriber_id')
        combined_df = pandas.merge(combined_df, subscribers_trial_inactive, how='left', on='subscriber_id')
        combined_df = pandas.merge(combined_df, subscribers_trial_end, how='left', on='subscriber_id')
        combined_df = pandas.merge(combined_df, subscribers_trial_patreon_convert, how='left', on='subscriber_id')
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

    def get_airtable_update_headers(self):
        headers = {
            'Authorization': f'Bearer {self.airtable_api_key}',
            'Content-Type': 'application/json' }
        return headers

    def update_trial_users_airtable(self):
        user_list_df = self.build_trial_user_list()

        # first, list records
        data_available = True
        airtable_records = []
        offset = None
        while data_available:
            url = self.airtable_trial_users_url
            if offset != None:
                url += '?offset=' + offset
            logging.info(f'querying airtable url {url}')
            response = requests.get(url, headers={'Authorization': f'Bearer {self.airtable_api_key}'})
            data = response.json()
            if 'offset' in data:
                offset = data['offset']
            else:
                data_available = False
            for record in data['records']:
                airtable_records.append({'id': record['id'], 'email': record['fields']['email']})
        airtable_records_df = pandas.DataFrame(airtable_records)

        combined_df = pandas.merge(airtable_records_df, user_list_df, how='inner', on='email')

        records = combined_df.to_dict(orient='records')

        update_instructions = [
            {'id': x['id'], 
            'fields': 
                {
                    'characters': x['characters'], 
                    'character_limit': x['character_limit'],
                    'trial_api_key': x['api_key'],
                    'tags': [x for x in [x[tag_column] for tag_column in self.tag_columns_list] if x != '']
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
        url = f'{self.airtable_trial_users_url}?view=tag%20requests'
        response = requests.get(url, headers={'Authorization': f'Bearer {self.airtable_api_key}'})
        data = response.json()
        airtable_records = []
        for record in data['records']:
            airtable_records.append({'id': record['id'], 'email': record['fields']['email'], 'tag_request': record['fields']['tag_request']})
        airtable_records_df = pandas.DataFrame(airtable_records)
        print(airtable_records_df)

        for index, row in airtable_records_df.iterrows():
            record_id = row['id']
            email = row['email']
            tag_request = row['tag_request']

            if tag_request == 'trial_extended':
                logging.info(f'extending trial for {email}')
                # increase API key character limit
                self.redis_connection.increase_trial_key_limit(email, quotas.TRIAL_EXTENDED_USER_CHARACTER_LIMIT)
                # tag user on convertkit
                self.convertkit_client.tag_user_trial_extended(email)
            else:
                tag_id = self.convertkit_client.tag_name_map[tag_request]                
                logging.info(f'tagging {email} with {tag_request} / {tag_id}')
                self.convertkit_client.tag_user(email, tag_id)
            # blank out tag_request field
            update_instructions = [
                {'id': record_id, 
                'fields': 
                    {
                        'tag_request': None
                    }
                }
            ]
            # upload to airtable
            response = requests.patch(self.airtable_trial_users_url, json={
                'records': update_instructions
            }, headers=self.get_airtable_update_headers())
            if response.status_code != 200:
                logging.error(response.content)





def main():
    raise Exception('should not be used anymore, replaced by user_utils.py')

    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                        datefmt='%Y%m%d-%H:%M:%S',
                        level=logging.INFO)

    parser = argparse.ArgumentParser(description='Utilities to manager trial users')
    choices = [
    'update_trial_users_airtable',
    'perform_airtable_tag_requests',
    'update_airtable'
    ]
    parser.add_argument('--action', choices=choices, help='Indicate what to do', required=True)
    parser.add_argument('--trial_email', help='email address of trial user')


    args = parser.parse_args()
    
    trial_users_utils = TrialUserUtils()

    if args.action == 'update_trial_users_airtable':
        trial_users_utils.update_trial_users_airtable()
    elif args.action == 'perform_airtable_tag_requests':
        trial_users_utils.perform_airtable_tag_requests()
    elif args.action == 'update_airtable':
        trial_users_utils.perform_airtable_tag_requests()
        trial_users_utils.update_trial_users_airtable()
    else:
        print(f'not recognized: {args.action}')


if __name__ == '__main__':
    main()