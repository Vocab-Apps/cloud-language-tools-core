import os
import sys
import logging
import pprint
import base64
import json
import tempfile
import shutil
import subprocess
import unittest
import pydub
import pydub.playback
# import epitran
# import pandas
import requests
import re
import secrets
# import redisdb

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import cloudlanguagetools
import cloudlanguagetools.servicemanager
import cloudlanguagetools.languages
import cloudlanguagetools.constants
import cloudlanguagetools.errors


def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure_default()
    return manager


def test_azure_audio():
    manager = get_manager()

    service = 'Azure'
    text = "this is a test sentence"
    voice_key = {
        'name': 'Microsoft Server Speech Text to Speech Voice (en-US, AriaNeural)'
    }

    result = manager.get_tts_audio(text, service, voice_key, {})
    permanent_file_name = 'azure_output.mp3'
    shutil.copyfile(result.name, permanent_file_name)
    print(f'tts result: {permanent_file_name}')
    # result = subprocess.run(['ffprobe', '-i', permanent_file_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # print(result.stderr)

def generate_video_audio():
    manager = get_manager()

    service = 'Azure'
    text = """Language Tools is an new Anki add-on designed to help you build language learning flashcards.
    It understands which languages you're studying and provides intelligent defaults. You can choose your favorite text to speech voice for each language,
    from a list of over 600 premium voices which cover more than 50 languages. <break time="2s"/> Once you're done, you can try translation. Language Tools offers high quality translation
    from neural network services such as Google, Microsoft, Amazon. It's really easy to use ! <break time="3s"/> You can also add text to speech audio to many cards at once.
    Just pick the source field, the target field, and click apply. Your audio is now getting added. <break time="2s"/> You will see the sound tag in your notes, and you will hear the sounds when reviewing.
    <break time="3s"/>
    Now, let's add a transliteration. This means going from one alphabet to another, for example for Chinese or Japanese to Latin alphabet. In this case, we're adding French IPA, or international phonetic alphabet pronunciations.
    <break time="2s"/>
    And now, let's add some new cards. All of the transformation you've added previously are memorized, and they'll be added to new cards too. Notice how the French to English translation, the sound, and the IPA pronunciation is added automatically.
    This is a huge time saver for people who create a lot of flashcards. You'll have more time to review your cards instead of spending most of your time creating them. No more excuses now !
    <break time="3s"/>
    You can see which transformations you've setup for your decks and remove them if needed.
    <break time="2s"/>
    And you can add those transformations all at once. That's right, add audio text to speech, translation and transliteration in one step. Again, a huge time saver for those who create a lot of cards
    Are you interested in trying it out ? Download Language Tools for Anki using the link below.
    <break time="1s"/>
    By the way, this is Microsoft Azure voice Aria, available on Language Tools.
    """

    text = """In this tutorial, we'll see how to add audio to your flashcards using batch generation. This means we will create some audio files which will be stored in your collection and will be played back when you review your cards.
    Let's first make sure our installation of Awesome TTS is working. Go to the Awesome TTS configuration, advanced, managed presets. Let's pick the Microsoft Azure service. Pick a french voice, type in some French text, then hit preview.
    <break time="1s"/>
    Now, let's go to the card browser. Select your deck, then select a few notes. Go to the Awesome TTS menu, then select add audio to selected notes.
    Make sure to pick a French voice from the Azure service. The source field should be front, that's the one which contains french text. The destination field should also be front, and the sound tag will be added alongside the french text.
    Note that we have the append option checked, as well as removing existing sound tag.
    Press Generate to start creating the audio files.
    Wait a little bit, it should be done soon.
    Let's look at our notes. You can see we now have a sound tag on the front field, after the french text. Let's hit preview for this note. The sound plays automatically, and we can play again using this play icon.
    The other cards should also have a sound tag.
    By the way, this is the Aria voice, available in Awesome TTS.
    """

    text = """etes vous vraiment malade ?"""

    voice_key = {
        'name': 'Microsoft Server Speech Text to Speech Voice (en-US, AriaNeural)'
    }

    voice_key = {
            "name": "Microsoft Server Speech Text to Speech Voice (fr-FR, HenriNeural)"
    }

    result = manager.get_tts_audio(text, service, voice_key, {})
    permanent_file_name = 'languagetools_video.mp3'
    permanent_file_name = 'french.mp3'
    shutil.copyfile(result.name, permanent_file_name)
    print(f'tts result: {permanent_file_name}')


def test_google_audio():
    manager = get_manager()

    service = 'Google'
    text = 'hello world test 1'

    voice_key = {
        'language_code': "en-US",
        'name': "en-US-Standard-C",
        'ssml_gender': "FEMALE"
    }

    result = manager.get_tts_audio(text, service, voice_key, {})
    permanent_file_name = 'google_output.mp3'
    shutil.copyfile(result.name, permanent_file_name)
    print(f'tts result: {permanent_file_name}')


def test_forvo_audio_tokipona():
    manager = get_manager()

    service = 'Forvo'
    text = 'kulupu'

    voice_key = {
        'language_code': "tok",
        'country_code': 'ANY'
    }

    result = manager.get_tts_audio(text, service, voice_key, {})
    permanent_file_name = 'google_output.mp3'
    shutil.copyfile(result.name, permanent_file_name)
    print(f'tts result: {permanent_file_name}')


def test_english_forvo():
    """Test Forvo English audio retrieval - similar to test_audio.py::test_english_forvo"""
    manager = get_manager()

    service = 'Forvo'
    text = 'absolutely'

    voice_key = {
        'language_code': 'en',
        'country_code': 'ANY'
    }

    result = manager.get_tts_audio(text, service, voice_key, {})
    permanent_file_name = 'forvo_english_output.mp3'
    shutil.copyfile(result.name, permanent_file_name)
    print(f'tts result: {permanent_file_name}')


def play_google_audio():
    manager = get_manager()

    service = 'Google'
    text = 'hello<break time="2s"/>world test 1'

    voice_key = {
        'language_code': "en-GB",
        'name': "en-GB-Wavenet-A",
        'ssml_gender': "FEMALE"
    }

    options = {'speaking_rate': 1.5} # 0.25 to 4.0
    options = {'pitch': 5} # -20.0 to 20.0
    options = {}
    result = manager.get_tts_audio(text, service, voice_key, options)
    filename = result.name
    music = pydub.AudioSegment.from_mp3(filename)
    pydub.playback.play(music)

def play_azure_audio():
    manager = get_manager()

    service = 'Azure'
    text = 'hello<break time="2s"/>world test 1'

    voice_key = {
        "name": "Microsoft Server Speech Text to Speech Voice (en-GB, MiaNeural)"
    }
    voice_key = {
        'name': 'Microsoft Server Speech Text to Speech Voice (en-US, AriaNeural)'
    }

    #options = {'speaking_rate': 1.5}
    #options = {'pitch': 5}
    # options = {'pitch': 100} # -100 to +100?
    # options = {'rate': 3.0} # 0.5 to 3 ?
    options = {}
    result = manager.get_tts_audio(text, service, voice_key, options)
    filename = result.name
    music = pydub.AudioSegment.from_mp3(filename)
    pydub.playback.play(music)

def test_gemini_rate_limit():
    """Generate Gemini audio in a loop to test rate limits"""
    import time

    manager = get_manager()

    service = 'Gemini'
    text = f"This is a test sentence to check Gemini TTS rate limits. Current time is {time.strftime('%Y-%m-%d %H:%M:%S')}."
    voice_key = {
        'name': 'Zephyr'  # Bright voice
    }
    options = {}

    print("=" * 80)
    print("Gemini TTS Rate Limit Test")
    print("=" * 80)
    print(f"Voice: {voice_key['name']}")
    print(f"Text: {text}")
    print("=" * 80)

    request_count = 0
    start_time = time.time()

    while True:
        request_count += 1
        request_start = time.time()

        try:
            result = manager.get_tts_audio(text, service, voice_key, options)
            elapsed = time.time() - request_start
            total_elapsed = time.time() - start_time

            print(f"Request {request_count}: SUCCESS in {elapsed:.2f}s "
                  f"(total: {total_elapsed:.1f}s, rate: {request_count/total_elapsed:.2f} req/s)")

            # Clean up the temp file
            if hasattr(result, 'name'):
                try:
                    os.unlink(result.name)
                except:
                    pass

        except Exception as e:
            elapsed = time.time() - request_start
            total_elapsed = time.time() - start_time

            error_type = type(e).__name__
            print(f"\nRequest {request_count}: {error_type} after {elapsed:.2f}s")
            print(f"  Total requests: {request_count}")
            print(f"  Total time: {total_elapsed:.1f}s")
            print(f"  Average rate before limit: {request_count/total_elapsed:.2f} req/s")
            print(f"  Error: {e}")

            # Check if it's a rate limit error with retry info
            if isinstance(e, cloudlanguagetools.errors.RateLimitRetryAfterError):
                print(f"  Retry after: {e.retry_after}s")
                print(f"\nWaiting {e.retry_after}s before continuing...")
                time.sleep(e.retry_after)
                print("Resuming...")
            else:
                # For other errors or rate limits without retry info, wait a bit and continue
                print("\nWaiting 5s before continuing...")
                time.sleep(5)
                print("Resuming...")


if __name__ == '__main__':
    logger = logging.getLogger()
    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])
    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y%m%d-%H:%M:%S',
                        stream=sys.stdout,
                        level=logging.DEBUG)

    if len(sys.argv) > 1:
        function_name = sys.argv[1]
        if function_name in globals() and callable(globals()[function_name]):
            globals()[function_name]()
        else:
            print(f"Function '{function_name}' not found or not callable")
    else:
        print("Please provide a function name as the first argument")
