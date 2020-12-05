
import os
import requests
import json


def get_token(subscription_key):
    fetch_token_url = "https://eastus.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key
    }
    response = requests.post(fetch_token_url, headers=headers)
    access_token = str(response.text)
    return access_token

def text_to_speech(text_input):
    azure_subscription_key = os.environ['AZURE_KEY']
    azure_region = os.environ['AZURE_REGION']
    speech_config = azure.cognitiveservices.speech.SpeechConfig(subscription=azure_subscription_key, region=azure_region)
    audio_config = azure.cognitiveservices.speech.audio.AudioOutputConfig(filename="output.wav")
    synthesizer = azure.cognitiveservices.speech.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    result = synthesizer.speak_text(text_input)
    print(result)
    print(result.cancellation_details)

def list_voices():
    azure_subscription_key = os.environ['AZURE_KEY']
    azure_region = os.environ['AZURE_REGION']

    access_token = get_token(azure_subscription_key)

    base_url = f'https://{azure_region}.tts.speech.microsoft.com/'
    path = 'cognitiveservices/voices/list'
    constructed_url = base_url + path
    headers = {
        'Authorization': 'Bearer ' + access_token,
    }        
    response = requests.get(constructed_url, headers=headers)
    if response.status_code == 200:
        voice_data = json.loads(response.content)
        print(voice_data)


