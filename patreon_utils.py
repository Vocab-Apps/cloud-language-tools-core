import os
import patreon


def list_campaigns(access_token):
    api_client = patreon.API(access_token)
    data = api_client.get_campaigns(10)
    print(data.json_data)



if __name__ == '__main__':
    access_token = os.environ['PATREON_ACCESS_TOKEN']
    list_campaigns(access_token)