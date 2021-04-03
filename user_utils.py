import pandas
import logging
import datetime

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


    def get_api_key_list_df(self):
        logging.info('listing API keys')
        api_key_list = self.redis_connection.list_api_keys()

        records = []
        for api_key_entry in api_key_list:
            data = {
                'api_key': api_key_entry['api_key']
            }
            data.update(api_key_entry['key_data'])
            records.append(data)
        data_df = pandas.DataFrame(records)
        data_df['expiration_dt'] = pandas.to_datetime(data_df['expiration'], unit='s')
        data_df['key_valid'] = data_df['expiration_dt'] > datetime.datetime.now()
        data_df = data_df.rename(columns={'user_id': 'patreon_user_id'})

        return data_df[['api_key', 'email', 'patreon_user_id', 'type', 'character_limit', 'expiration_dt', 'key_valid']]

    def get_patreon_users_df(self):
        user_list = self.patreon_utils.get_patreon_user_ids()
        user_list_df = pandas.DataFrame(user_list)
        user_list_df = user_list_df.rename(columns={'user_id': 'patreon_user_id'})
        return user_list_df

    def build_user_data(self):
        api_key_list_df = self.get_api_key_list_df()
        print(api_key_list_df)
        patreon_user_df = self.get_patreon_users_df()
        print(patreon_user_df)

        combined_df = pandas.merge(api_key_list_df, patreon_user_df, how='left', on='patreon_user_id')
        print(combined_df)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                        datefmt='%Y%m%d-%H:%M:%S',
                        level=logging.INFO)
    user_utils = UserUtils()

    user_utils.build_user_data()
    # user_utils.get_patreon_users_df()