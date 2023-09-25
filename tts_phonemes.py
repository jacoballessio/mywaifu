import argparse
import base64
import json
import os
from phonemizer.backend import EspeakBackend
from phonemizer.punctuation import Punctuation
from phonemizer.separator import Separator

from phonemizer import phonemize
from datetime import datetime
from google.cloud import texttospeech
import time
from google.auth.transport.requests import Request
import requests
import json
import base64
from google.oauth2 import service_account
from io import BytesIO
from pydub import AudioSegment
import subprocess
import os
import whisper


PHONEME_TO_IMAGE_MAPPING = {
    # Vowels and Diphthongs
    "iː": "E.png",
    "ɪ": "E.png",
    "e": "E.png",
    "eɪ": "E.png",
    "æ": "A.png",
    "aː": "A.png",
    "aɪ": "A.png",
    "ɒ": "O.png",
    "ɔː": "O.png",
    "oʊ": "O.png",
    "ʊ": "UQ.png",
    "uː": "UQ.png",
    "ʌ": "UQ.png",
    "aʊ": "A.png",
    "ɔɪ": "O.png",
    "ə": "A.png", # Schwa

    # Consonants and others
    "b": "MBP.png",
    "d": "TS.png",
    "f": "FV.png",
    "g": "TS.png",
    "h": "TS.png",
    "j": "TS.png",
    "k": "TS.png",
    "l": "LN.png",
    "m": "MBP.png",
    "n": "LN.png",
    "p": "MBP.png",
    "r": "WR.png",
    "s": "TS.png",
    "ʃ": "TS.png", # 'sh' sound
    "t": "TS.png",
    "tʃ": "TS.png", # 'ch' sound
    "θ": "TS.png", # 'th' as in 'think'
    "ð": "TS.png", # 'th' as in 'that'
    "v": "FV.png",
    "w": "WR.png",
    "z": "TS.png",
    "ʒ": "TS.png", # 's' in 'measure'
    "ŋ": "TS.png"  # 'ng' sound as in 'song'
}
# For using the mapping:
def phoneme_to_image(phoneme):
    return "/build/static/media/lip_shapes/" + PHONEME_TO_IMAGE_MAPPING.get(phoneme, 'TS.png')

    return mouth_shapes_and_timings
from multiprocessing import Pool

def get_phoneme_words_and_mouth_shapes(timepoints, text, audio_dur, multiplier):
    mouth_shapes_and_timings = []
    backend = EspeakBackend('en-us')
    timepoints_len = len(timepoints)
    
    phns = phonemize(
        text,
        language='en-us',
        backend='espeak',
        separator=Separator(phone="|", word=' ', syllable=None),
        strip=True,
        preserve_punctuation=True,
        njobs=4)
    
    phoneme_words = phns.split()

    if len(phoneme_words) != timepoints_len:
        return "Length mismatch between phoneme words and timepoints."

    for i in range(timepoints_len):
        if i == timepoints_len - 1:
            next_end = audio_dur
        else:
            next_end = timepoints[i+1][1]
        
        start_time = max(0, timepoints[i][1] * multiplier)
        end_time = max(0.1, next_end * multiplier)
        
        phoneme_word = phoneme_words[i]
        phonemes_in_word = phoneme_word.split("|")
        phoneme_count = len(phonemes_in_word)
        
        phoneme_duration = abs((end_time - start_time) / phoneme_count)

        for j, phoneme in enumerate(phonemes_in_word):
            phoneme_image = phoneme_to_image(phoneme)
            start_t = start_time + j * phoneme_duration
            end_t = start_time + (j + 1) * phoneme_duration
            mouth_shapes_and_timings.append((phoneme_image, start_t, end_t))
        
    return mouth_shapes_and_timings

def obtain_access_token(service_account_file):
    """Obtain an access token using a service account file."""
    credentials = service_account.Credentials.from_service_account_file(
        service_account_file,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(Request())
    return credentials.token

def insert_marks(text):
    """Inserts SSML mark tags for each word in the input text."""
    words = text.split()
    marked_words = [f'<mark name="mark_{i}"/>{word}' for i, word in enumerate(words)]
    return '<speak>' + ' '.join(marked_words) + '</speak>'

def get_audio_duration(decoded_audio: str) -> float:
    """Returns the duration of a base64 encoded audio in seconds using FFmpeg."""

    with BytesIO(decoded_audio) as audio_file:
        # Write the audio data to a temporary file
        with open("temp_audio.mp3", "wb") as f:
            f.write(audio_file.read())

        # Run FFmpeg to get the audio duration
        result = subprocess.run(["ffmpeg", "-i", "temp_audio.mp3", "-f", "null", "-"], capture_output=True, text=True)

        # Extract duration from FFmpeg output
        for line in result.stderr.split('\n'):
            if "Duration:" in line:
                duration_str = line.split(",")[0].split("Duration:")[1].strip()
                hours, minutes, seconds = duration_str.split(":")
                total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                return total_seconds

    return None  # If failed to get duration

def synthesize_text_with_timepoints(text, service_account_file):
    # Obtain an access token
    token = obtain_access_token(service_account_file)

    # API endpoint
    url = "https://texttospeech.googleapis.com/v1beta1/text:synthesize"
    #remove emojis from text
    text = text.encode('ascii', 'ignore').decode('ascii')
    # Process the text to include marks for each word
    ssml_text = insert_marks(text)


    # Prepare the payload
    payload = {
    "input": {"ssml": ssml_text},
    "voice": {
        "languageCode": "en-US",       # Set the language to Japanese
        "name": "en-US-Neural2-G",    # Specify the voice name
        "ssmlGender": "FEMALE",       # Keep the gender as NEUTRAL or adjust if needed
    },
    "audioConfig": {"audioEncoding": "MP3", "pitch": 2, "speakingRate": 1.4},
    "enableTimePointing": ["SSML_MARK"]
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        data = response.json()
        audio_content = base64.b64decode(data['audioContent'])
        timepoints = [(item['markName'], item['timeSeconds']) for item in data.get('timepoints', [])]
        return audio_content, timepoints, ssml_text
    else:


        return None, None, None


def get_tts_and_info(text):
    SERVICE_ACCOUNT_FILE = "service-account.json"
    #if text is all spaces, replace with random text

    audio_content, timepoints, ssml_text = synthesize_text_with_timepoints(text, SERVICE_ACCOUNT_FILE)
    audio_file = f"build/static/media/{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
    #first create the directory if it doesn't exist
    if not os.path.exists("build/static/media/"):
        os.makedirs("build/static/media/")
    #write the audio content to the file
    with open(audio_file, "wb") as f:
        f.write(audio_content)
    
    audio_dur = get_audio_duration(audio_content)-0.8

    #for some reason, the timepoints don't properly end when the audio ends. Do combat this, we will calculate a multiplier based on the duration/last timepoint. This multiplier will be used to multiply the start and end time of each lip shape.
    #multiplier = audio_dur/timepoints[-1][1]
    try:
        multiplier = audio_dur/timepoints[-1][1]
    except:
        multiplier = 1


    return audio_file, timepoints, audio_dur, multiplier, ssml_text


if __name__ == '__main__':

    #get args
    parser = argparse.ArgumentParser(description='Process some text.')
    parser.add_argument('--text', type=str, help='text to be synthesized')
    args = parser.parse_args()
    text = args.text

    #get the audio file, timepoints, and audio duration
    audio_file, timepoints, audio_dur, multiplier, ssml_text = get_tts_and_info(text)


