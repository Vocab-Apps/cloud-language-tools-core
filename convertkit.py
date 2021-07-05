import os
import requests
import logging
import pprint
import secrets
import cloudlanguagetools.constants

class ConvertKit():
    def __init__(self):
        self.api_key = os.environ['CONVERTKIT_API_KEY']
        self.api_secret = os.environ['CONVERTKIT_API_SECRET']

        self.tag_id_api_requested = int(os.environ['CONVERTKIT_TRIAL_API_KEY_REQUESTED_TAG'])
        self.tag_id_api_ready = int(os.environ['CONVERTKIT_TRIAL_API_KEY_READY_TAG'])
        self.tag_id_patreon_api_ready = int(os.environ['CONVERTKIT_PATREON_API_KEY_READY_TAG'])
        self.tag_id_trial_extended = int(os.environ['CONVERTKIT_TRIAL_EXTENDED_TAG'])
        self.tag_id_trial_inactive = int(os.environ['CONVERTKIT_TRIAL_INACTIVE_TAG'])
        self.tag_id_trial_user = int(os.environ['CONVERTKIT_TRIAL_USER_TAG'])
        self.tag_id_trial_end_reach_out = int(os.environ['CONVERTKIT_TRIAL_END_REACH_OUT_TAG'])
        self.tag_id_trial_patreon_convert = int(os.environ['CONVERTKIT_TRIAL_PATREON_CONVERT_TAG'])
        self.tag_id_patreon = int(os.environ['CONVERTKIT_PATREON_USER_TAG'])

        self.enable = secrets.config['convertkit']['enable']
        if self.enable:
            self.getcheddar_user_form_id = secrets.config['convertkit']['getcheddar_user_form_id']
            self.tag_id_getcheddar_user = secrets.config['convertkit']['tag_ig_getchedar_user']

        self.enable_debounce = secrets.config['debounce']['enable']
        if self.enable_debounce:
            self.debounce_email = secrets.config['debounce']['email']
            self.debounce_api_key = secrets.config['debounce']['api_key']

        self.tag_name_map = {
            'trial_patreon_convert': self.tag_id_trial_patreon_convert,
            'trial_end_reach_out': self.tag_id_trial_end_reach_out,
            'trial_user_inactive': self.tag_id_trial_inactive 
        }


        self.full_tag_id_map = {} 

    def email_valid(self, email):
        if not self.enable_debounce:
            return True
        try:
            url = "https://api.debounce.io/v1/"
            querystring = {'api': self.debounce_api_key, 'email': email}
            response = requests.get(url, params=querystring)
            if response.status_code == 200:
                data = response.json()
                if data['debounce']['result'] == 'Invalid' and data['debounce']['reason'] == 'Disposable':
                    logging.info(f'found disposable email: {email}')
                    return False
            else:
                logging.error(f'received error: {response.status_code}: {response.text}')
        except:
            logging.exception(f'could not perform debounce query to validate {email}')
        return True # true by default


    def register_getcheddar_user(self, email, api_key):
        if self.enable:
            logging.info(f'registering new getcheddar user on convertkit')
            url = f'https://api.convertkit.com/v3/forms/{self.getcheddar_user_form_id}/subscribe'
            response = requests.post(url, json={
                    "api_key": self.api_key,
                    "email": email,
                    'fields' : {
                        'getcheddar_api_key': api_key
                    }
            }, timeout=cloudlanguagetools.constants.RequestTimeout)
            if response.status_code != 200:
                logging.error(f'could not subscribe user to form: {response.content}')


    def tag_user_api_ready(self, email, api_key):
        url = f'https://api.convertkit.com/v3/tags/{self.tag_id_api_ready}/subscribe'
        response = requests.post(url, json={
                "api_key": self.api_key,
                "email": email,
                'fields' : {
                    'trial_api_key': api_key
                }
        }, timeout=cloudlanguagetools.constants.RequestTimeout)
        if response.status_code != 200:
            logging.error(f'could not tag user: {response.content}')

    def tag_user_patreon_api_ready(self, email, api_key):
        url = f'https://api.convertkit.com/v3/tags/{self.tag_id_patreon_api_ready}/subscribe'
        response = requests.post(url, json={
                "api_key": self.api_key,
                "email": email,
                'fields' : {
                    'patreon_api_key': api_key
                }
        }, timeout=cloudlanguagetools.constants.RequestTimeout)
        if response.status_code != 200:
            logging.error(f'could not tag user: {response.content}')



    def tag_user(self, email, tag_id):
        url = f'https://api.convertkit.com/v3/tags/{tag_id}/subscribe'
        response = requests.post(url, json={
                "api_key": self.api_key,
                "email": email
        }, timeout=cloudlanguagetools.constants.RequestTimeout)
        if response.status_code != 200:
            logging.error(f'could not tag user: {response.content}')            
        else:
            logging.info(f'tagged user with tag_id {tag_id}: {email}')

    def tag_user_trial_extended(self, email):
        self.tag_user(email, self.tag_id_trial_extended)

    def tag_user_trial_inactive(self, email):
        self.tag_user(email, self.tag_id_trial_inactive)

    def list_subscribers_tag(self, tag_id):
        subscriber_list = []

        url = f'https://api.convertkit.com/v3/tags/{tag_id}/subscriptions?api_secret={self.api_secret}&page=1'
        response = requests.get(url)
        data = response.json()
        current_page = data['page']
        total_pages = data['total_pages']


        for data in data['subscriptions']:
            subscriber = data['subscriber']
            subscriber_list.append(subscriber)

        while current_page < total_pages:
            next_page = current_page + 1
            url = f'https://api.convertkit.com/v3/tags/{tag_id}/subscriptions?api_secret={self.api_secret}&page={next_page}'
            response = requests.get(url)
            data = response.json()
            current_page = data['page']

            for data in data['subscriptions']:
                subscriber = data['subscriber']
                subscriber_list.append(subscriber)

        return subscriber_list

    def list_canceled(self):
        canceled_list = []

        url = f'https://api.convertkit.com/v3/subscribers?api_secret={self.api_secret}&sort_field=cancelled_at'
        response = requests.get(url)
        data = response.json()

        current_page = data['page']
        total_pages = data['total_pages']

        canceled_list.extend(data['subscribers'])

        while current_page < total_pages:
            next_page = current_page + 1
            url = f'https://api.convertkit.com/v3/subscribers?api_secret={self.api_secret}&sort_field=cancelled_at&page={next_page}'
            response = requests.get(url)
            data = response.json()
            current_page = data['page']
            canceled_list.extend(data['subscribers'])

        return canceled_list

    def list_trial_users(self):
        return self.list_subscribers_tag(self.tag_id_trial_user)

    def list_patreon_users(self):
        return self.list_subscribers_tag(self.tag_id_patreon)

    def list_getcheddar_users(self):
        return self.list_subscribers_tag(self.tag_id_getcheddar_user)

    def list_tags(self, subscriber_id):
        url = f'https://api.convertkit.com/v3/subscribers/{subscriber_id}/tags?api_secret={self.api_secret}'
        response = requests.get(url)
        data = response.json()
        return data['tags']

    def populate_tag_map(self):
        logging.info('populating tag map')
        url = f'https://api.convertkit.com/v3/tags?api_key={self.api_key}'
        response = requests.get(url)
        assert response.status_code == 200
        data = response.json()
        tags = data['tags']
        for tag_entry in tags:
            tag_name = tag_entry['name']
            tag_id = tag_entry['id']
            self.full_tag_id_map[tag_name] = tag_id