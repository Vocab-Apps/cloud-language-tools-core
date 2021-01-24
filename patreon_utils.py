import os
import patreon


def list_campaigns(access_token, campaign_id):
    api_client = patreon.API(access_token)
    # data = api_client.get_campaigns(10)
    data = api_client.get_campaigns_by_id_members(campaign_id, 10, includes=['user'])
    print(data.json_data)



if __name__ == '__main__':
    access_token = os.environ['PATREON_ACCESS_TOKEN']
    campaign_id = os.environ['PATREON_CAMPAIGN_ID']
    list_campaigns(access_token, campaign_id)