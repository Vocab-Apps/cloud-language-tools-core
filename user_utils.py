import pandas
import logging

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
        return pandas.DataFrame(records)

    def get_patreon_users_df(self):
        self.patreon_utils.get_patreon_user_ids()
        return None

    def build_user_data(self):
        api_key_list_df = self.get_api_key_list_df()
        print(api_key_list_df)
        patreon_user_df = self.get_patreon_users_df()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                        datefmt='%Y%m%d-%H:%M:%S',
                        level=logging.INFO)
    user_utils = UserUtils()

    # user_utils.build_user_data()
    user_utils.get_patreon_users_df()