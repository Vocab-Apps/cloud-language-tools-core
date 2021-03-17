import os
import requests
import logging
import cloudlanguagetools.constants

class ConvertKit():
    def __init__(self):
        self.api_key = os.environ['CONVERTKIT_API_KEY']
        self.api_secret = os.environ['CONVERTKIT_API_SECRET']

        self.tag_id_api_requested = int(os.environ['CONVERTKIT_TRIAL_API_KEY_REQUESTED_TAG'])
        self.tag_id_api_ready = int(os.environ['CONVERTKIT_TRIAL_API_KEY_READY_TAG'])
        self.tag_id_trial_extended = int(os.environ['CONVERTKIT_TRIAL_EXTENDED_TAG'])

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

    def tag_user_trial_extended(self, email):
        url = f'https://api.convertkit.com/v3/tags/{self.tag_id_trial_extended}/subscribe'
        response = requests.post(url, json={
                "api_key": self.api_key,
                "email": email
        }, timeout=cloudlanguagetools.constants.RequestTimeout)
        if response.status_code != 200:
            logging.error(f'could not tag user: {response.content}')            

    def list_subscribers(self):
        # curl https://api.convertkit.com/v3/subscribers?api_secret=<your_secret_api_key>&from=2016-02-01&to=2015-02-28
        url = f'https://api.convertkit.com/v3/subscribers?api_secret={self.api_secret}'
        response = requests.get(url)
        data = response.json()
        assert(data['total_pages'] == 1)
        return data['subscribers']

    def list_tags(self, subscriber_id):
        url = f'https://api.convertkit.com/v3/subscribers/{subscriber_id}/tags?api_secret={self.api_secret}'
        response = requests.get(url)
        data = response.json()
        return data['tags']