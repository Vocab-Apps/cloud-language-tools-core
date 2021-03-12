import os
import requests
import pprint

api_key = os.environ['CONVERTKIT_API_KEY']
api_secret = os.environ['CONVERTKIT_API_SECRET']


def list_subscribers():
    # curl https://api.convertkit.com/v3/subscribers?api_secret=<your_secret_api_key>&from=2016-02-01&to=2015-02-28
    url = f'https://api.convertkit.com/v3/subscribers?api_secret={api_secret}'
    response = requests.get(url)
    data = response.json()
    pprint.pprint(data)    

def view_subscriber():
    url = f'https://api.convertkit.com/v3/subscribers/1215642036?api_secret={api_secret}'
    response = requests.get(url)
    data = response.json()
    pprint.pprint(data)    

def list_tags_subscriber():
    # curl https://api.convertkit.com/v3/subscribers/<subscriber_id>/tags?api_key=<your_public_api_key>
    url = f'https://api.convertkit.com/v3/subscribers/1215642036/tags?api_secret={api_secret}'
    response = requests.get(url)
    data = response.json()
    pprint.pprint(data)        


def tag_subscriber():
    # curl -X POST https://api.convertkit.com/v3/tags/<tag_id>/subscribe\
    #      -H "Content-Type: application/json; charset=utf-8"\
    #      -d '{ \
    #             "api_key": "<your_public_api_key>",\
    #             "email": "jonsnow@example.com"\
    #          }'    
    url = f'https://api.convertkit.com/v3/tags/{2248152}/subscribe'
    response = requests.post(url, json={
            "api_key": api_key,
            "email": "dustpuppy4@airpost.net"
    })
    print(response)
    print(response.content)
    data = response.json()
    pprint.pprint(data)    

def list_tags():
    url = f'https://api.convertkit.com/v3/tags?api_key={api_key}'
    response = requests.get(url)
    data = response.json()
    pprint.pprint(data)


def configure_addtag_webhook():
    # curl -X POST https://api.convertkit.com/v3/automations/hooks
    #      -H 'Content-Type: application/json'\
    #      -d '{ "api_secret": "<your_secret_api_key>",\
    #            "target_url": "http://example.com/incoming",\
    #            "event": { "name": "subscriber.subscriber_activate" } }'    

    url = 'https://api.convertkit.com/v3/automations/hooks'
    response = requests.post(url, json={
        'api_secret': api_secret,
        'target_url': 'https://bfa7c6b87809.ngrok.io/convertkit_subscriber_request_trial_key',
        'event': {  'name': 'subscriber.tag_add', 'tag_id': 2248152 }
    })
    print(response)
    print(response.content)
    data = response.json()
    pprint.pprint(data)


if __name__ == '__main__':
    configure_addtag_webhook()
    # list_tags()
    # list_subscribers()
    # view_subscribers()
    # list_tags_subscriber()
    # tag_subscriber()