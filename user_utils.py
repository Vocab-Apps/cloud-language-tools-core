import pandas
import logging
import datetime
import argparse

import redisdb
import airtable_utils
import patreon_utils
import convertkit
import redisdb


class UserUtils():
    def __init__(self):
        self.airtable_utils = airtable_utils.AirtableUtils()
        self.patreon_utils = patreon_utils.PatreonUtils()
        self.convertkit_client = convertkit.ConvertKit()
        self.redis_connection = redisdb.RedisDb()


    def get_api_key_list_df(self, key_type):
        logging.info('listing API keys')
        api_key_list = self.redis_connection.list_api_keys()

        records = []
        for api_key_entry in api_key_list:
            api_key = api_key_entry['api_key']
            key_data = api_key_entry['key_data']
            if key_data['type'] == key_type:
                data = {
                    'api_key': api_key
                }
                data.update(key_data)
                records.append(data)
        data_df = pandas.DataFrame(records)
        data_df['expiration_dt'] = pandas.to_datetime(data_df['expiration'], unit='s')
        data_df['expiration_str'] = data_df['expiration_dt'].dt.strftime('%Y-%m-%d')
        data_df['key_valid'] = data_df['expiration_dt'] > datetime.datetime.now()
        data_df = data_df.rename(columns={'user_id': 'patreon_user_id', 'expiration_str': 'api_key_expiration', 'key_valid': 'api_key_valid'})

        field_list_map = {
            'patreon': ['api_key', 'email', 'patreon_user_id', 'api_key_valid', 'api_key_expiration']
        }

        return data_df[field_list_map[key_type]]

    def get_patreon_users_df(self):
        user_list = self.patreon_utils.get_patreon_user_ids()
        user_list_df = pandas.DataFrame(user_list)
        user_list_df = user_list_df.rename(columns={'user_id': 'patreon_user_id'})
        return user_list_df

    def get_usage_data(self):
        scan_pattern = 'usage:user:monthly:202103'
        usage_entries = self.redis_connection.list_usage(scan_pattern)
        # clt:usage:user:monthly:202103:Amazon:translation:2m0xzH92tgxb0pk9
        records = []
        for entry in usage_entries:
            usage_key = entry['usage_key']
            components = usage_key.split(':')
            api_key = components[-1]
            service = components[5]
            request_type = components[6]
            records.append({
                'api_key': api_key,
                'service': service,
                'request_type': request_type,
                'characters': int(entry['characters'])
            })

        records_df = pandas.DataFrame(records)

        cost_table = [
            {
                'service': 'Azure',
                'request_type': 'audio',
                'character_cost': (1.0/1000000) * 16
            },
            {
                'service': 'Google',
                'request_type': 'audio',
                'character_cost': (1.0/1000000) * 16
            },            
        ]

        cost_table_df = pandas.DataFrame(cost_table)

        combined_df = pandas.merge(records_df, cost_table_df, how='left', on=['service', 'request_type'])
        combined_df['cost'] = combined_df['character_cost'] * combined_df['characters']

        print(combined_df)


    def build_user_data_patreon(self):
        # api keys
        api_key_list_df = self.get_api_key_list_df('patreon')
        # print(api_key_list_df)
        
        # patreon data
        patreon_user_df = self.get_patreon_users_df()
        # print(patreon_user_df)

        # usage data
        usage_data_df = self.get_usage_data()

        combined_df = pandas.merge(api_key_list_df, patreon_user_df, how='outer', on='patreon_user_id')

        return combined_df

    def update_airtable_patreon(self):
        user_data_df = self.build_user_data_patreon()

        # get airtable patreon users table
        airtable_patreon_df = self.airtable_utils.get_patreon_users()
        airtable_patreon_df = airtable_patreon_df[['record_id', 'User ID']]

        joined_df = pandas.merge(airtable_patreon_df, user_data_df, how='left', left_on='User ID', right_on='patreon_user_id')

        update_df = joined_df[['record_id', 'entitled', 'api_key', 'api_key_valid', 'api_key_expiration']]
        update_df = update_df.fillna({
            'api_key': '',
            'api_key_valid': False,
            'entitled': False
        })

        self.airtable_utils.update_patreon_users(update_df)




    

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                        datefmt='%Y%m%d-%H:%M:%S',
                        level=logging.INFO)
    user_utils = UserUtils()

    parser = argparse.ArgumentParser(description='User Utils')
    choices = [
        'update_airtable_patreon',
        'usage_data'
    ]
    parser.add_argument('--action', choices=choices, help='Indicate what to do', required=True)
    args = parser.parse_args()

    if args.action == 'update_airtable_patreon':
        user_utils.update_airtable_patreon()
    elif args.action == 'usage_data':
        user_utils.get_usage_data()
