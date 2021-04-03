import os
import pandas
import logging
import requests

class AirtableUtils():
    def __init__(self):
        self.airtable_api_key = os.environ['AIRTABLE_API_KEY']
        self.airtable_trial_users_url = os.environ['AIRTABLE_TRIAL_USERS_URL']
        self.airtable_patron_users_url = os.environ['AIRTABLE_PATREON_USERS_URL']

    def get_trial_users(self):
        return self.get_airtable_records(self.airtable_trial_users_url)

    def get_patreon_users(self):
        return self.get_airtable_records(self.airtable_patron_users_url)

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

    

