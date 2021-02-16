import os
import patreon
import redisdb
import argparse

def user_authorized(oauth_code):
    client_id = os.environ['PATREON_CLIENT_ID']
    client_secret = os.environ['PATREON_CLIENT_SECRET']
    redirect_uri = os.environ['PATREON_REDIRECT_URI']

    creator_access_token = os.environ['PATREON_ACCESS_TOKEN']
    campaign_id = os.environ['PATREON_CAMPAIGN_ID']

    oauth_client = patreon.OAuth(client_id, client_secret)
    tokens = oauth_client.get_tokens(oauth_code, redirect_uri)
    print(tokens)
    access_token = tokens['access_token']

    api_client = patreon.API(access_token)

    user_authorized = False

    user_response = api_client.get_identity(includes=['memberships', 'campaign'], fields={'user': ['email']})
    # print(user_response)
    user_data = user_response.json_data
    # print(user_data)
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

def get_entitled_users(creator_access_token, campaign_id):
    api_client = patreon.API(creator_access_token)
    memberships = []
    entitled_members = []
    cursor = None
    while True:
        members_response = api_client.get_campaigns_by_id_members(campaign_id, 900, cursor=cursor, includes=['user', 'currently_entitled_tiers'], fields={'user': ['email', 'full_name']})
        # print(members_response.json_data)
        for member in members_response.json_data['data']:
            if len(member['relationships']['currently_entitled_tiers']['data']) > 0:
                entitled_members.append(member)
        try:
            cursor = api_client.extract_cursor(members_response)
            if not cursor:
                break
        except:
            # no more data
            break

    # print(entitled_members[0])
    entitled_user_ids = [x['relationships']['user']['data']['id'] for x in entitled_members]
    print(f'number of currently entitled users: {len(entitled_user_ids)}')    
    return entitled_user_ids
    

def list_patreon_user_ids(creator_access_token, campaign_id):
    entitled_user_ids = get_entitled_users(creator_access_token, campaign_id)
    redis_connection = redisdb.RedisDb()
    api_key_list = redis_connection.list_api_keys()
    # retain patreon keys
    # print(api_key_list[0])
    # print(entitled_user_ids)
    api_key_list = [x for x in api_key_list if 'type' in x['key_data'] and x['key_data']['type'] == 'patreon']
    print('keys for entitled users:')
    result = []
    for api_key_entry in api_key_list:
        patreon_user_id = api_key_entry['key_data']['user_id']
        email = api_key_entry['key_data']['email']
        key_valid = api_key_entry['validity']
        user_entitled = patreon_user_id in entitled_user_ids
        print(f'user_id: {patreon_user_id} email: {email} key_valid: {key_valid} user_entitled: {user_entitled}')
        if user_entitled:
            result.append(api_key_entry)
    # print(api_key_list)

    return result

def extend_user_key_validity(creator_access_token, campaign_id):
    api_key_list = list_patreon_user_ids(creator_access_token, campaign_id)
    redis_connection = redisdb.RedisDb()
    for api_key_entry in api_key_list:
        patreon_user_id = api_key_entry['key_data']['user_id']
        email = api_key_entry['key_data']['email']
        print(f'extending validity for {patreon_user_id}, {email}')
        redis_connection.get_patreon_user_key(patreon_user_id, email)


def list_campaigns(access_token, campaign_id):
    api_client = patreon.API(access_token)
    # data = api_client.get_campaigns(10)
    data = api_client.get_campaigns_by_id_members(campaign_id, 10, includes=['user', 'currently_entitled_tiers'])
    print(data.json_data)



if __name__ == '__main__':
    access_token = os.environ['PATREON_ACCESS_TOKEN']
    campaign_id = os.environ['PATREON_CAMPAIGN_ID']

    parser = argparse.ArgumentParser(description='Patreon Utils')
    choices = ['list_patreon_entitled_users', 'extend_key_validity']
    parser.add_argument('--action', choices=choices, help='Indicate what to do', required=True)
    args = parser.parse_args()

    if args.action == 'list_patreon_entitled_users':
        list_patreon_user_ids(access_token, campaign_id)
    elif args.action == 'extend_key_validity':
        extend_user_key_validity(access_token, campaign_id)

    

    