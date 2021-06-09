import pandas
import logging
import datetime
import argparse
import json

import quotas
import redisdb
import airtable_utils
import patreon_utils
import getcheddar_utils
import convertkit
import redisdb
import cloudlanguagetools.constants


class UserUtils():
    def __init__(self):
        self.airtable_utils = airtable_utils.AirtableUtils()
        self.patreon_utils = patreon_utils.PatreonUtils()
        self.convertkit_client = convertkit.ConvertKit()
        self.redis_connection = redisdb.RedisDb()
        self.getcheddar_utils = getcheddar_utils.GetCheddarUtils()

    def get_full_api_key_list(self):
        logging.info('getting full API key list')
        api_key_list = self.redis_connection.list_api_keys()
        return api_key_list        


    def get_api_key_list_df(self, api_key_list, key_type):

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
        if 'expiration' in data_df:
            data_df['expiration_dt'] = pandas.to_datetime(data_df['expiration'], unit='s')
            data_df['expiration_str'] = data_df['expiration_dt'].dt.strftime('%Y-%m-%d')
            data_df['key_valid'] = data_df['expiration_dt'] > datetime.datetime.now()
            data_df = data_df.rename(columns={'user_id': 'patreon_user_id', 'expiration_str': 'api_key_expiration', 'key_valid': 'api_key_valid'})

        field_list_map = {
            'patreon': ['api_key', 'email', 'patreon_user_id', 'api_key_valid', 'api_key_expiration'],
            'trial': ['api_key', 'email', 'api_key_valid', 'api_key_expiration'],
            'getcheddar': ['api_key', 'email', 'code']
        }

        return data_df[field_list_map[key_type]]

    

    def get_patreon_users_df(self):
        logging.info(f'getting patreon user data')
        user_list = self.patreon_utils.get_patreon_user_ids()
        user_list_df = pandas.DataFrame(user_list)
        user_list_df = user_list_df.rename(columns={'user_id': 'patreon_user_id'})
        return user_list_df

    # get monthly usage data per user
    # -------------------------------

    def get_monthly_usage_data(self):
        logging.info('getting current month usage data')
        pattern = 'usage:user:monthly:' + datetime.datetime.now().strftime("%Y%m")
        return self.get_usage_data(pattern, 'monthly_cost', 'monthly_chars')

    def get_prev_monthly_usage_data(self):
        logging.info('getting previous month usage data')
        prev_month_datetime = datetime.datetime.now() + datetime.timedelta(days=-31)
        pattern = 'usage:user:monthly:' + prev_month_datetime.strftime("%Y%m")
        return self.get_usage_data(pattern, 'prev_monthly_cost', 'prev_monthly_chars')

    # get global monthly usage data
    # -----------------------------

    def get_global_monthly_usage_data(self):
        logging.info('getting current global month usage data')
        pattern = 'usage:global:monthly'
        return self.get_global_usage_data(pattern)

    # get global daily usage data
    # ---------------------------

    def get_global_daily_usage_data(self):
        logging.info('getting previous global daily usage data')
        pattern = 'usage:global:daily'
        return self.get_global_usage_data(pattern)

    def get_daily_usage_data(self):
        pattern = 'usage:user:daily:' + datetime.datetime.now().strftime("%Y%m%d")
        return self.get_usage_data(pattern, 'daily_cost', 'daily_chars')

    def get_usage_data(self, usage_key_pattern, cost_field_name, characters_field_name):
        usage_entries = self.redis_connection.list_usage(usage_key_pattern)
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

        if len(records) == 0:
            return pandas.DataFrame()

        records_df = pandas.DataFrame(records)

        cost_table_df = pandas.DataFrame(quotas.COST_TABLE)

        combined_df = pandas.merge(records_df, cost_table_df, how='left', on=['service', 'request_type'])
        combined_df[cost_field_name] = combined_df['character_cost'] * combined_df['characters']
        combined_df = combined_df.rename(columns={'characters': characters_field_name})

        grouped_df = combined_df.groupby('api_key').agg({cost_field_name: 'sum', characters_field_name: 'sum'}).reset_index()
        return grouped_df

    def get_global_usage_data(self, usage_key_pattern):
        usage_entries = self.redis_connection.list_usage(usage_key_pattern)
        # print(usage_entries)
        # clt:usage:global:monthly:202103:Amazon:translation
        records = []
        for entry in usage_entries:
            usage_key = entry['usage_key']
            components = usage_key.split(':')
            period = components[4]
            service = components[5]
            request_type = components[6]
            records.append({
                'period': period,
                'service': service,
                'request_type': request_type,
                'characters': int(entry['characters']),
                'requests': int(entry['requests'])
            })

        records_df = pandas.DataFrame(records)
        # print(records_df)

        cost_table_df = pandas.DataFrame(quotas.COST_TABLE)

        combined_df = pandas.merge(records_df, cost_table_df, how='left', on=['service', 'request_type'])
        combined_df['cost'] = combined_df['character_cost'] * combined_df['characters']

        # retain certain columns
        combined_df = combined_df[['period', 'service', 'request_type', 'cost', 'characters',  'requests']]

        return combined_df

    def get_user_tracking_data(self, api_key_list):
        logging.info('getting user tracking data')

        def process_languages(hash_data):
            language_list = hash_data.keys()
            language_name_list = [cloudlanguagetools.constants.Language[x].lang_name for x in language_list]            
            return language_name_list

        def process_tag(hash_data):
            return list(hash_data.keys())

        processing_map = {
            redisdb.KEY_TYPE_USER_AUDIO_LANGUAGE: process_languages,
            redisdb.KEY_TYPE_USER_SERVICE: process_tag,
            redisdb.KEY_TYPE_USER_CLIENT: process_tag,
            redisdb.KEY_TYPE_USER_CLIENT_VERSION: process_tag
        }

        field_name_map = {
            redisdb.KEY_TYPE_USER_AUDIO_LANGUAGE: 'detected_languages',
            redisdb.KEY_TYPE_USER_SERVICE: 'services',
            redisdb.KEY_TYPE_USER_CLIENT: 'clients',
            redisdb.KEY_TYPE_USER_CLIENT_VERSION: 'versions',
        }

        record_lists = self.redis_connection.list_user_tracking_data(api_key_list)
        processed_records_dict = {}

        for key, records in record_lists.items():
            field_name = field_name_map[key]
            processing_fn = processing_map[key]
            for record in records:
                api_key = record['api_key']
                if api_key not in processed_records_dict:
                    processed_records_dict[api_key] = {
                        'api_key': api_key
                    }
                processed_records_dict[api_key][field_name] = processing_fn(record['data'])

        record_list = list(processed_records_dict.values())
        return pandas.DataFrame(record_list)

    def build_user_data_patreon(self):
        # api keys
        api_key_list = self.get_full_api_key_list()

        api_key_list_df = self.get_api_key_list_df(api_key_list, 'patreon')
        # print(api_key_list_df)
        
        # get user tracking data
        tracking_data_df = self.get_user_tracking_data(api_key_list)

        # patreon data
        patreon_user_df = self.get_patreon_users_df()
        # print(patreon_user_df)

        # get tag data from convertkit
        convertkit_users_df = self.get_convertkit_patreon_users()
        tag_data_df = self.get_convertkit_tag_data()
        convertkit_data_df = pandas.merge(convertkit_users_df, tag_data_df, how='left', on='subscriber_id')

        # usage data
        monthly_usage_data_df = self.get_monthly_usage_data()
        prev_monthly_usage_data_df = self.get_prev_monthly_usage_data()

        combined_df = pandas.merge(api_key_list_df, patreon_user_df, how='outer', on='patreon_user_id')
        combined_df = pandas.merge(combined_df, convertkit_data_df, how='left', on='email')
        combined_df = pandas.merge(combined_df, monthly_usage_data_df, how='left', on='api_key')
        combined_df = pandas.merge(combined_df, prev_monthly_usage_data_df, how='left', on='api_key')
        combined_df = pandas.merge(combined_df, tracking_data_df, how='left', on='api_key')

        self.update_tags_convertkit_users(combined_df)

        return combined_df

    def build_global_usage_data(self):
        monthly_usage_data_df = self.get_global_monthly_usage_data()
        return monthly_usage_data_df

    def build_global_daily_usage_data(self):
        usage_df = self.get_global_daily_usage_data()
        return usage_df

    def get_convertkit_trial_users(self):
        subscribers = self.convertkit_client.list_trial_users()
        return self.get_dataframe_from_subscriber_list(subscribers)

    def get_convertkit_patreon_users(self):
        logging.info(f'getting list of patreon users from convertkit')
        subscribers = self.convertkit_client.list_patreon_users()
        return self.get_dataframe_from_subscriber_list(subscribers)

    def get_convertkit_canceled_users(self):
        canceled_list = self.convertkit_client.list_canceled()
        canceled_df = self.get_dataframe_from_subscriber_list(canceled_list)
        canceled_df['canceled'] = True
        canceled_df = canceled_df[['subscriber_id', 'canceled']]
        return canceled_df

    def get_dataframe_from_subscriber_list(self, subscribers):
        users = []
        for subscriber in subscribers:
            users.append({
                'subscriber_id': subscriber['id'],
                'email': subscriber['email_address']
            })
        users_df = pandas.DataFrame(users)
        return users_df

    def get_convertkit_dataframe_for_tag(self, tag_id, tag_name):
        logging.info(f'getting dataframe for tag {tag_name}')
        subscribers = self.convertkit_client.list_subscribers_tag(tag_id)
        if len(subscribers) == 0:
            return pandas.DataFrame()
        data_df = self.get_dataframe_from_subscriber_list(subscribers)
        data_df[tag_name] = tag_name
        data_df = data_df[['subscriber_id', tag_name]]
        return data_df

    def get_convertkit_tag_data(self):
        logging.info(f'getting convertkit tag data')
        self.convertkit_client.populate_tag_map()

        # we are not interested in these tags
        tag_ignore_list = ['patreon_api_key_ready', 
        'patreon_canceled', 
        'patreon_canceled',
        'patreon_user',
        'trial_api_key_ready',
        'trial_api_key_requested',
        'trial_user']

        tag_id_map = {tag_name:tag_id for tag_name, tag_id in self.convertkit_client.full_tag_id_map.items() if tag_name not in tag_ignore_list}
        present_tags = []

        dataframe_list = []
        for tag_name, tag_id in tag_id_map.items():
            data_df = self.get_convertkit_dataframe_for_tag(tag_id, tag_name)
            if len(data_df) > 0:
                dataframe_list.append(data_df)
                present_tags.append(tag_name)

        first_dataframe = dataframe_list[0]
        other_dataframes = dataframe_list[1:]
        combined_df = first_dataframe
        for data_df in other_dataframes:
            combined_df = pandas.merge(combined_df, data_df, how='outer', on='subscriber_id')
        combined_df = combined_df.fillna('')

        combined_records = []

        def get_row_tag_array(row, present_tags):
            result = []
            for tag_name in present_tags:
                result.append(row[tag_name])
            return result

        for index, row in combined_df.iterrows():
            tags = get_row_tag_array(row, present_tags)
            tags = [x for x in tags if len(x) > 0]
            combined_records.append({
                'subscriber_id': row['subscriber_id'],
                'tags': tags
            })

        final_df = pandas.DataFrame(combined_records)

        return final_df

    def build_user_data_trial(self):
        # api keys
        api_key_list = self.get_full_api_key_list()
        flat_api_key_list = [x['api_key'] for x in api_key_list]

        api_key_list_df = self.get_api_key_list_df(api_key_list, 'trial')

        # get convertkit subscriber ids
        convertkit_trial_users_df = self.get_convertkit_trial_users()

        # get convertkit canceled users
        canceled_df = self.get_convertkit_canceled_users()

        # get tag data from convertkit
        tag_data_df = self.get_convertkit_tag_data()

        # get user tracking data
        tracking_data_df = self.get_user_tracking_data(api_key_list)
        
        # get character entitlement
        entitlement = self.redis_connection.get_trial_user_entitlement(flat_api_key_list)
        entitlement_df = pandas.DataFrame(entitlement)
        # get usage
        api_key_usage = self.redis_connection.get_trial_user_usage(flat_api_key_list)
        api_key_usage_df = pandas.DataFrame(api_key_usage)

        combined_df = pandas.merge(api_key_list_df, tracking_data_df, how='left', on='api_key')
        combined_df = pandas.merge(combined_df, convertkit_trial_users_df, how='left', on='email')
        combined_df = pandas.merge(combined_df, canceled_df, how='left', on='subscriber_id')
        combined_df = pandas.merge(combined_df, tag_data_df, how='left', on='subscriber_id')
        combined_df = pandas.merge(combined_df, api_key_usage_df, how='left', on='api_key')
        combined_df = pandas.merge(combined_df, entitlement_df, how='left', on='api_key')

        combined_df['canceled'] = combined_df['canceled'].fillna(False)

        combined_df['characters'] = combined_df['characters'].fillna(0)
        combined_df['character_limit'] = combined_df['character_limit'].fillna(0)

        combined_df['characters'] =  combined_df['characters'].astype(int)
        combined_df['character_limit'] = combined_df['character_limit'].astype(int)

        self.update_tags_convertkit_users(combined_df)

        return combined_df

    def build_user_data_getcheddar(self):
        # api keys
        api_key_list = self.get_full_api_key_list()
        flat_api_key_list = [x['api_key'] for x in api_key_list]

        api_key_list_df = self.get_api_key_list_df(api_key_list, cloudlanguagetools.constants.ApiKeyType.getcheddar.name)

        # get user tracking data
        tracking_data_df = self.get_user_tracking_data(api_key_list)

        # usage data
        monthly_usage_data_df = self.get_monthly_usage_data()
        prev_monthly_usage_data_df = self.get_prev_monthly_usage_data()

        combined_df = pandas.merge(api_key_list_df, tracking_data_df, how='left', on='api_key')
        if len(monthly_usage_data_df) > 0:
            combined_df = pandas.merge(combined_df, monthly_usage_data_df, how='left', on='api_key')
        if len(prev_monthly_usage_data_df) > 0:
            combined_df = pandas.merge(combined_df, prev_monthly_usage_data_df, how='left', on='api_key')

        # do this when we're in production
        # self.update_tags_convertkit_users(combined_df)

        return combined_df

    def update_tags_convertkit_users(self, data_df):
        # perform necessary taggings on convertkit
        
        # make the logic a bit easier by removing nans
        data_df['tags'] = data_df['tags'].fillna("").apply(list)
        data_df['clients'] = data_df['clients'].fillna("").apply(list)

        for index, row in data_df.iterrows():
            email = row['email']
            tags = row['tags']
            clients = row['clients']

            for client in clients:
                tag_name = f'client_{client}'
                if tag_name in self.convertkit_client.full_tag_id_map:
                    if tag_name not in tags:
                        logging.info(f'tagging {email} with {tag_name}')
                        tag_id = self.convertkit_client.full_tag_id_map[tag_name]
                        self.convertkit_client.tag_user(email, tag_id)

    def perform_airtable_trial_tag_requests(self):
        airtable_records_df = self.airtable_utils.get_trial_tag_requests()

        airtable_update_records = []

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
            airtable_update_records.append({
                'record_id': record_id,
                'tag_request': None
            })
        
        if len(airtable_update_records) > 0:
            airtable_update_df = pandas.DataFrame(airtable_update_records)
            self.airtable_utils.update_trial_users(airtable_update_df)


    def update_airtable_patreon(self):
        logging.info('updating airtable for patreon users')

        user_data_df = self.build_user_data_patreon()

        # get airtable patreon users table
        airtable_patreon_df = self.airtable_utils.get_patreon_users()
        airtable_patreon_df = airtable_patreon_df[['record_id', 'User ID']]

        joined_df = pandas.merge(airtable_patreon_df, user_data_df, how='left', left_on='User ID', right_on='patreon_user_id')

        update_df = joined_df[['record_id', 'entitled', 'api_key', 'api_key_valid', 'api_key_expiration', 'monthly_cost', 'monthly_chars', 'prev_monthly_cost', 'prev_monthly_chars', 'detected_languages', 'services', 'clients', 'versions']]
        update_df = update_df.fillna({
            'api_key': '',
            'api_key_valid': False,
            'entitled': False
        })

        self.airtable_utils.update_patreon_users(update_df)

    def update_airtable_trial(self):
        logging.info('updating airtable for trial users')

        self.perform_airtable_trial_tag_requests()

        user_data_df = self.build_user_data_trial()

        # get airtable trial users table
        airtable_trial_df = self.airtable_utils.get_trial_users()
        airtable_trial_df = airtable_trial_df[['record_id', 'email']]

        joined_df = pandas.merge(airtable_trial_df, user_data_df, how='left', left_on='email', right_on='email')

        update_df = joined_df[['record_id', 'api_key', 'characters', 'character_limit', 'detected_languages', 'services', 'clients', 'versions', 'tags', 'canceled']]

        # print(update_df)

        self.airtable_utils.update_trial_users(update_df)

    def update_airtable_usage(self):
        usage_df = self.build_global_usage_data()
        self.airtable_utils.update_usage(usage_df)
        usage_df = self.build_global_daily_usage_data()
        self.airtable_utils.update_usage_daily(usage_df)

    def update_airtable_all(self):
        self.update_airtable_patreon()
        self.update_airtable_trial()
        self.update_airtable_usage()
    
    def extend_patreon_key_validity(self):
        logging.info('extending patreon key validity')
        self.patreon_utils.extend_user_key_validity()

    def report_getcheddar_usage_all_users(self):
        api_key_list = self.redis_connection.list_getcheddar_api_keys()
        for api_key in api_key_list:
            self.report_getcheddar_user_usage(api_key)

    def report_getcheddar_user_usage(self, api_key):
        logging.info(f'reporting getcheddar usage for api key {api_key}')
        user_data = self.redis_connection.get_api_key_data(api_key)
        # retrieve the accumulated usage
        usage_slice = self.redis_connection.get_getcheddar_usage_slice(api_key)
        usage = self.redis_connection.get_usage_slice_data(usage_slice)
        thousand_char_quantity = usage['characters'] / quotas.GETCHEDDAR_CHAR_MULTIPLIER
        updated_user_data = self.getcheddar_utils.report_customer_usage(user_data['code'], thousand_char_quantity)
        # this will update the usage on the api_key_data
        self.redis_connection.get_update_getcheddar_user_key(updated_user_data)
        # reset the usage slice
        self.redis_connection.reset_getcheddar_usage_slice(api_key)
        

    def download_audio_requests(self):
        audio_request_list = self.redis_connection.retrieve_audio_requests()
        audio_requests = [json.loads(x) for x in audio_request_list]
        # voice_key should be a string
        for request in audio_requests:
            request['voice'] = json.dumps(request['voice_key'])

        audio_requests_df = pandas.DataFrame(audio_requests)
        filename = 'temp_data_files/audio_requests.csv'
        audio_requests_df.to_csv(filename)

        logging.info(f'wrote audio requests to {filename}')
        return

        # print(audio_requests_df)

        # find duplicate requests
        # duplicate_df = audio_requests_df[audio_requests_df.duplicated(['text'])]
        # print(duplicate_df)

        # grouped_df = duplicate_df.groupby(['text']).agg({'language_code': 'count'}).reset_index()
        # print(grouped_df)

        grouped_df = audio_requests_df.groupby(['text', 'language_code', 'service', 'voice', 'api_key']).agg({'request_mode':'count'}).reset_index()
        grouped_df = grouped_df.sort_values(by='request_mode', ascending=False)
        print(grouped_df.head(50))

        if False:
            grouped_df = audio_requests_df.groupby(['text', 'language_code']).agg({'request_mode':'count'}).reset_index()
            grouped_df = grouped_df.sort_values(by='request_mode', ascending=False)
            print(grouped_df.head(50))        


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                        datefmt='%Y%m%d-%H:%M:%S',
                        level=logging.INFO)
    user_utils = UserUtils()

    parser = argparse.ArgumentParser(description='User Utils')
    choices = [
        'update_airtable_all',
        'update_airtable_patreon',
        'update_airtable_trial',
        'update_airtable_usage',
        'show_getcheddar_user_data',
        'extend_patreon_key_validity',
        'usage_data',
        'report_getcheddar_usage_all_users',
        'show_patreon_user_data',
        'show_trial_user_data',
        'download_audio_requests'
    ]
    parser.add_argument('--action', choices=choices, help='Indicate what to do', required=True)
    args = parser.parse_args()

    if args.action == 'update_airtable_all':
        user_utils.update_airtable_all()
    elif args.action == 'update_airtable_patreon':
        user_utils.update_airtable_patreon()
    if args.action == 'update_airtable_trial':
        user_utils.update_airtable_trial()
    if args.action == 'update_airtable_usage':
        user_utils.update_airtable_usage()
    elif args.action == 'show_patreon_user_data':
        user_data_df = user_utils.build_user_data_patreon()
        print(user_data_df)
    elif args.action == 'show_trial_user_data':
        user_data_df = user_utils.build_user_data_trial()
        print(user_data_df)
    elif args.action == 'show_getcheddar_user_data':
        user_data_df = user_utils.build_user_data_getcheddar()
        print(user_data_df)        
    elif args.action == 'extend_patreon_key_validity':
        user_utils.extend_patreon_key_validity()    
    elif args.action == 'usage_data':
        # user_utils.build_global_usage_data()
        data_df = user_utils.build_global_daily_usage_data()
        print(data_df)
    elif args.action == 'report_getcheddar_usage_all_users':
        user_utils.report_getcheddar_usage_all_users()
    elif args.action == 'download_audio_requests':
        user_utils.download_audio_requests()
