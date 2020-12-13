#!/usr/bin/env python3

from flask import Flask, request
from flask_restful import Resource, Api, inputs
import json
import cloudlanguagetools.servicemanager

app = Flask(__name__)
api = Api(app)

manager = cloudlanguagetools.servicemanager.ServiceManager()
manager.configure()    

class LanguageList(Resource):
    def get(self):
        return manager.get_language_list()

class VoiceList(Resource):
    def get(self):
        return manager.get_tts_voice_list_json()

class TranslationLanguageList(Resource):
    def get(self):
        return manager.get_translation_language_list_json()

class Translate(Resource):
    def post(self):
        data = request.json
        return {'translated_text': manager.get_translation(data['text'], data['service'], data['from_language_key'], data['to_language_key'])}

class Detect(Resource):
    def post(self):
        data = request.json
        text_list = data['text_list']
        result = manager.detect_language(text_list)
        return {'detected_language': result.name}

api.add_resource(LanguageList, '/language_list')
api.add_resource(VoiceList, '/voice_list')
api.add_resource(TranslationLanguageList, '/translation_language_list')
api.add_resource(Translate, '/translate')
api.add_resource(Detect, '/detect')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')