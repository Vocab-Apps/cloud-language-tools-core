#!/usr/bin/env python3

from flask import Flask, request, send_file, jsonify
import flask_restful
import json
import functools
import os
import cloudlanguagetools.servicemanager
import cloudlanguagetools.errors
import redisdb
import patreon
import patreon.schemas

app = Flask(__name__)
api = flask_restful.Api(app)

manager = cloudlanguagetools.servicemanager.ServiceManager()
manager.configure()

redis_connection = redisdb.RedisDb()

def authenticate(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('api_key', None)
        # is this API key valid ?
        result = redis_connection.api_key_valid(api_key)
        if result['key_valid']:
            # authentication successful
            return func(*args, **kwargs)
        return {'error': result['msg']}, 401
    return wrapper


class LanguageList(flask_restful.Resource):
    def get(self):
        return manager.get_language_list()

class VoiceList(flask_restful.Resource):
    def get(self):
        return manager.get_tts_voice_list_json()

class TranslationLanguageList(flask_restful.Resource):
    def get(self):
        return manager.get_translation_language_list_json()

class TransliterationLanguageList(flask_restful.Resource):
    def get(self):
        return manager.get_transliteration_language_list_json()

class Translate(flask_restful.Resource):
    method_decorators = [authenticate]
    def post(self):
        try:
            data = request.json
            return {'translated_text': manager.get_translation(data['text'], data['service'], data['from_language_key'], data['to_language_key'])}
        except cloudlanguagetools.errors.RequestError as err:
            return {'error': str(err)}, 400

class TranslateAll(flask_restful.Resource):
    method_decorators = [authenticate]
    def post(self):
        try:
            data = request.json
            return manager.get_all_translations(data['text'], data['from_language'], data['to_language'])
        except cloudlanguagetools.errors.RequestError as err:
            return {'error': str(err)}, 400

class Transliterate(flask_restful.Resource):
    method_decorators = [authenticate]
    def post(self):
        try:
            data = request.json
            return {'transliterated_text': manager.get_transliteration(data['text'], data['service'], data['transliteration_key'])}
        except cloudlanguagetools.errors.RequestError as err:
            return {'error': str(err)}, 400    

class Detect(flask_restful.Resource):
    method_decorators = [authenticate]
    def post(self):
        data = request.json
        text_list = data['text_list']
        result = manager.detect_language(text_list)
        return {'detected_language': result.name}

class Audio(flask_restful.Resource):
    method_decorators = [authenticate]
    def post(self):
        data = request.json
        audio_temp_file = manager.get_tts_audio(data['text'], data['service'], data['voice_key'], data['options'])
        return send_file(audio_temp_file.name, mimetype='audio/mpeg')

class VerifyApiKey(flask_restful.Resource):
    def post(self):
        data = request.json
        api_key = data['api_key']
        result = redis_connection.api_key_valid(api_key)
        return result

class PatreonKey(flask_restful.Resource):
    def get(self):
        client_id = os.environ['PATREON_CLIENT_ID']
        client_secret = os.environ['PATREON_CLIENT_SECRET']
        redirect_uri = os.environ['PATREON_REDIRECT_URI']

        creator_access_token = os.environ['PATREON_ACCESS_TOKEN']
        campaign_id = os.environ['PATREON_CAMPAIGN_ID']

        oauth_client = patreon.OAuth(client_id, client_secret)
        tokens = oauth_client.get_tokens(request.args.get('code'), redirect_uri)
        access_token = tokens['access_token']

        api_client = patreon.API(access_token)

        user_authorized = False

        user_response = api_client.get_identity(includes=['memberships', 'campaign'])
        user_data = user_response.json_data
        print(f'user_data: {user_data}')
        user_id = user_data['data']['id']
        print(f'user_id: {user_id}')
        
        # check for memberships
        memberships = user_data['data']['relationships']['memberships']['data']
        if len(memberships) > 0:
            print(memberships[0])
            membership_id = memberships[0]['id']

            # obtain info about this membership:
            creator_api_client = patreon.API(creator_access_token)
            membership_data = creator_api_client.get_members_by_id(membership_id, includes=['currently_entitled_tiers'])

            enabled_tiers = membership_data.json_data['data']['relationships']['currently_entitled_tiers']['data']
            if len(enabled_tiers) > 0:
                enabled_tier = enabled_tiers[0]
                user_tier_id = enabled_tier['id']

                # make sure this is one of the tiers of the campaign
                campaign_data = creator_api_client.get_campaigns_by_id(campaign_id, includes=['tiers'])
                print(f'campaign_data: {campaign_data.json_data}')
                # {'data': {'attributes': {}, 'id': '3214584', 'relationships': {'tiers': {'data': [{'id': '4087058', 'type': 'tier'}, {'id': '4087060', 'type': 'tier'}]}},
                tier_list = campaign_data.json_data['data']['relationships']['tiers']['data']
                tier_set = {tier['id']:True for tier in tier_list}

                if user_tier_id in tier_set:
                    user_authorized = True



            # {'data': {'attributes': {}, 'id': 'ff8e86a7-9038-4fe8-a75a-9abcf837973e', 'relationships': {'currently_entitled_tiers': {'data': [{'id': '4087058', 'type': 'tier'}]}}, 'type': 'member'}, 'included': [{'attributes': {}, 'id': '4087058', 'type': 'tier'}], 'links': {'self': 'https://www.patreon.com/api/oauth2/v2/members/ff8e86a7-9038-4fe8-a75a-9abcf837973e'}}

            # obtain info about the campaign



        return f'user_authorized: {user_authorized}'

api.add_resource(LanguageList, '/language_list')
api.add_resource(VoiceList, '/voice_list')
api.add_resource(TranslationLanguageList, '/translation_language_list')
api.add_resource(TransliterationLanguageList, '/transliteration_language_list')
api.add_resource(Translate, '/translate')
api.add_resource(TranslateAll, '/translate_all')
api.add_resource(Transliterate, '/transliterate')
api.add_resource(Detect, '/detect')
api.add_resource(Audio, '/audio')
api.add_resource(VerifyApiKey, '/verify_api_key')
api.add_resource(PatreonKey, '/patreon_key')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')