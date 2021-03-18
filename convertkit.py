import os
import requests
import logging
import pprint
import cloudlanguagetools.constants

class ConvertKit():
    def __init__(self):
        self.api_key = os.environ['CONVERTKIT_API_KEY']
        self.api_secret = os.environ['CONVERTKIT_API_SECRET']

        self.tag_id_api_requested = int(os.environ['CONVERTKIT_TRIAL_API_KEY_REQUESTED_TAG'])
        self.tag_id_api_ready = int(os.environ['CONVERTKIT_TRIAL_API_KEY_READY_TAG'])
        self.tag_id_trial_extended = int(os.environ['CONVERTKIT_TRIAL_EXTENDED_TAG'])
        self.tag_id_trial_inactive = int(os.environ['CONVERTKIT_TRIAL_INACTIVE_TAG'])

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

    def list_subscribers(self):
        # curl https://api.convertkit.com/v3/subscribers?api_secret=<your_secret_api_key>&from=2016-02-01&to=2015-02-28
        subscriber_list = []

        
        url = f'https://api.convertkit.com/v3/subscribers?api_secret={self.api_secret}&page=1'
        response = requests.get(url)
        data = response.json()
        current_page = data['page']
        total_pages = data['total_pages']

        subscriber_list.extend(data['subscribers'])

        while current_page < total_pages:
            next_page = current_page + 1
            url = f'https://api.convertkit.com/v3/subscribers?api_secret={self.api_secret}&page={next_page}'
            response = requests.get(url)
            data = response.json()
            current_page = data['page']
            subscriber_list.extend(data['subscribers'])

        return subscriber_list

    def list_tags(self, subscriber_id):
        url = f'https://api.convertkit.com/v3/subscribers/{subscriber_id}/tags?api_secret={self.api_secret}'
        response = requests.get(url)
        data = response.json()
        return data['tags']