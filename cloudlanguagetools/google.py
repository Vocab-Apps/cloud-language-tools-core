import google.cloud.texttospeech
import cloudlanguagetools.service

class GoogleService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def get_tts_voice_list(self):
        print('google.get_tts_voice_list')
        client = google.cloud.texttospeech.TextToSpeechClient()

        # Performs the list voices request
        voices = client.list_voices()

        for voice in voices.voices:
            # Display the voice's name. Example: tpc-vocoded
            print(f"Name: {voice.name}")

            # Display the supported language codes for this voice. Example: "en-US"
            for language_code in voice.language_codes:
                print(f"Supported language: {language_code}")

            ssml_gender = google.cloud.texttospeech.SsmlVoiceGender(voice.ssml_gender)

            # Display the SSML Voice Gender
            print(f"SSML Voice Gender: {ssml_gender.name}")

            # Display the natural sample rate hertz for this voice. Example: 24000
            print(f"Natural Sample Rate Hertz: {voice.natural_sample_rate_hertz}\n")
        