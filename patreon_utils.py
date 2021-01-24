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

    user_response = api_client.get_identity(includes=['memberships', 'campaign'], fields={'user': ['email']})
    # print(user_response)
    user_data = user_response.json_data
    print(user_data)
    user_id = user_data['data']['id']
    user_email = user_data['data']['attributes']['email']
    
    # check for memberships
    memberships = user_data['data']['relationships']['memberships']['data']
    if len(memberships) > 0:
        # print(memberships[0])
        membership_id = memberships[0]['id']

        # obtain info about this membership:
        creator_api_client = patreon.API(creator_access_token)
        membership_data = creator_api_client.get_members_by_id(membership_id, includes=['currently_entitled_tiers','user'], fields={'user': ['full_name', 'email']})
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

    return {'authorized': user_authorized, 'user_id': user_id, 'email': user_email}

def get_campaign_members(creator_access_token, campaign_id):
    api_client = patreon.API(creator_access_token)
    memberships = []
    members = []
    cursor = None
    while True:
        members_response = api_client.get_campaigns_by_id_members(campaign_id, 900, cursor=cursor, includes=['user'], fields={'user': ['email', 'full_name']})
        # print(members_response.json_data)
        for member in members_response.json_data['data']:
            members.append(member)
            print(member)
        # members += members_response.data()
        cursor = api_client.extract_cursor(members_response)
        print(cursor)
        if not cursor:
            break

    
    # names_and_membershipss = [{
    #     'full_name': member.relationship('user').attribute('full_name'),
    #     'amount_cents': member.attribute('amount_cents'),
    # } for member in members]    


def list_campaigns(access_token, campaign_id):
    api_client = patreon.API(access_token)
    # data = api_client.get_campaigns(10)
    data = api_client.get_campaigns_by_id_members(campaign_id, 10, includes=['user', 'currently_entitled_tiers'])
    print(data.json_data)



if __name__ == '__main__':
    access_token = os.environ['PATREON_ACCESS_TOKEN']
    campaign_id = os.environ['PATREON_CAMPAIGN_ID']
    # list_campaigns(access_token, campaign_id)
    get_campaign_members(access_token, campaign_id)