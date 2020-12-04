
import os
import azure.cognitiveservices.speech
import azure.cognitiveservices.speech.audio

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