import os
import patreon

def user_authorized(oauth_code):
    client_id = os.environ['PATREON_CLIENT_ID']
    client_secret = os.environ['PATREON_CLIENT_SECRET']
    redirect_uri = os.environ['PATREON_REDIRECT_URI']

    creator_access_token = os.environ['PATREON_ACCESS_TOKEN']
    campaign_id = os.environ['PATREON_CAMPAIGN_ID']

    oauth_client = patreon.OAuth(client_id, client_secret)
    tokens = oauth_client.get_tokens(oauth_code, redirect_uri)
    access_token = tokens['access_token']

    api_client = patreon.API(access_token)

    user_authorized = False

    user_response = api_client.get_identity(includes=['memberships', 'campaign'])
    # print(user_response)
    user_data = user_response.json_data
    # print(user_data)
    user_id = user_data['data']['id']
    
    # check for memberships
    memberships = user_data['data']['relationships']['memberships']['data']
    if len(memberships) > 0:
        # print(memberships[0])
        membership_id = memberships[0]['id']

        # obtain info about this membership:
        creator_api_client = patreon.API(creator_access_token)
        membership_data = creator_api_client.get_members_by_id(membership_id, includes=['currently_entitled_tiers'])
        # print(f'membership_data: {membership_data.json_data}')

        enabled_tiers = membership_data.json_data['data']['relationships']['currently_entitled_tiers']['data']
        if len(enabled_tiers) > 0:
            enabled_tier = enabled_tiers[0]
            user_tier_id = enabled_tier['id']

            # make sure this is one of the tiers of the campaign
            campaign_data = creator_api_client.get_campaigns_by_id(campaign_id, includes=['tiers'])
            tier_list = campaign_data.json_data['data']['relationships']['tiers']['data']
            tier_set = {tier['id']:True for tier in tier_list}

            if user_tier_id in tier_set:
                user_authorized = True

    return {'authorized': user_authorized, 'user_id': user_id}


def list_campaigns(access_token, campaign_id):
    api_client = patreon.API(access_token)
    # data = api_client.get_campaigns(10)
    data = api_client.get_campaigns_by_id_members(campaign_id, 10, includes=['user', 'currently_entitled_tiers'])
    print(data.json_data)



if __name__ == '__main__':
    access_token = os.environ['PATREON_ACCESS_TOKEN']
    campaign_id = os.environ['PATREON_CAMPAIGN_ID']
    list_campaigns(access_token, campaign_id)