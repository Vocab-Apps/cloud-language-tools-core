import os
import pandas
import logging
import requests
import pprint

class AirtableUtils():
    def __init__(self):
        self.airtable_api_key = os.environ['AIRTABLE_API_KEY']
        self.airtable_trial_users_url = os.environ['AIRTABLE_TRIAL_USERS_URL']
        self.airtable_patreon_users_url = os.environ['AIRTABLE_PATREON_USERS_URL']
        self.airtable_usage_url = os.environ['AIRTABLE_USAGE_URL']

    def get_trial_users(self):
        return self.get_airtable_records(self.airtable_trial_users_url)

    def get_trial_tag_requests(self):
        url = f'{self.airtable_trial_users_url}?view=tag%20requests'
        response = requests.get(url, headers={'Authorization': f'Bearer {self.airtable_api_key}'})
        data = response.json()
        airtable_records = []
        for record in data['records']:
            airtable_records.append({'id': record['id'], 'email': record['fields']['email'], 'tag_request': record['fields']['tag_request']})
        airtable_records_df = pandas.DataFrame(airtable_records)
        return airtable_records_df

    def get_patreon_users(self):
        return self.get_airtable_records(self.airtable_patreon_users_url)

    def get_airtable_records(self, base_url):
        # first, list records
        data_available = True
        airtable_records = []
        offset = None
        while data_available:
            url = base_url
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
                # print(record)
                full_record = {'record_id': record['id']}
                full_record.update(record['fields'])
                airtable_records.append(full_record)
        airtable_records_df = pandas.DataFrame(airtable_records)
        return airtable_records_df

    def update_patreon_users(self, data_df):
        self.update_airtable_records(self.airtable_patreon_users_url, data_df)

    def update_trial_users(self, data_df):
        self.update_airtable_records(self.airtable_trial_users_url, data_df)

    def update_usage(self, usage_df):
        # self.airtable_usage_url
        self.create_airtable_records(self.airtable_usage_url, usage_df)

    def update_airtable_records(self, base_url, update_df):

        update_instructions = []
        column_list = update_df.columns.values.tolist()
        column_list.remove('record_id')

        for index, record in update_df.iterrows():
            update_instruction = {
                'id': record['record_id'],
                'fields': {}
            }
            for column in column_list:
                value = record[column]
                if isinstance(record[column], list):
                    pass # don't do anything
                elif pandas.isnull(value):
                    value = None
                update_instruction['fields'][column] = value
            update_instructions.append(update_instruction)

        logging.info(f'starting to update {base_url}')

        headers = {
            'Authorization': f'Bearer {self.airtable_api_key}',
            'Content-Type': 'application/json' }
        while len(update_instructions) > 0:
            slice_length = min(10, len(update_instructions))
            update_slice = update_instructions[0:slice_length]
            del update_instructions[0:slice_length]
            
            # pprint.pprint(update_slice)
            logging.info(f'updating records')
            response = requests.patch(base_url, json={
                'records': update_slice,
                'typecast': True
            }, headers=headers)
            if response.status_code != 200:
                logging.error(response.content)        

    def delete_all_airtable_records(records, base_url):


    def create_airtable_records(self, base_url, records_df):

        update_instructions = []
        column_list = records_df.columns.values.tolist()

        for index, record in records_df.iterrows():
            create_instruction = {
                'fields': {}
            }
            for column in column_list:
                value = record[column]
                if isinstance(record[column], list):
                    pass # don't do anything
                elif pandas.isnull(value):
                    value = None
                create_instruction['fields'][column] = value
            update_instructions.append(create_instruction)

        logging.info(f'starting to update {base_url}')

        headers = {
            'Authorization': f'Bearer {self.airtable_api_key}',
            'Content-Type': 'application/json' }
        while len(update_instructions) > 0:
            slice_length = min(10, len(update_instructions))
            update_slice = update_instructions[0:slice_length]
            del update_instructions[0:slice_length]
            
            # pprint.pprint(update_slice)
            logging.info(f'creating records')
            response = requests.post(base_url, json={
                'records': update_slice,
                'typecast': True
            }, headers=headers)
            if response.status_code != 200:
                logging.error(response.content)            