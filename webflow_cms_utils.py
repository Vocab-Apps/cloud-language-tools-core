import requests
import secrets

class WebflowCMSUtils():
    def __init__(self):
        self.api_key = secrets.config['webflow']['api_key']

    def get_headers(self):
        return {
            'Authorization': f'Bearer {self.api_key}',
            'accept-version': '1.0.0'
        }

    def get_auth_info(self):
        url = 'https://api.webflow.com/info'
        response = requests.get(url,headers=self.get_headers())
        print(response.json())


if __name__ == '__main__':
    webflow_utils = WebflowCMSUtils()
    webflow_utils.get_auth_info()
