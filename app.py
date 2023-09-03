from flask import Flask, render_template, request, jsonify
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
import openai
import os

#set openai key to OPENAI_API_KEY environment variable
openai.api_key = os.environ.get("OPENAI_API_KEY")

app = Flask(__name__)
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

def insert_marks(text):
    """Inserts SSML mark tags for each word in the input text."""
    words = text.split()
    marked_words = [f'<mark name="mark_{i}"/>{word}' for i, word in enumerate(words)]
    return '<speak>' + ' '.join(marked_words) + '</speak>'


def obtain_access_token(service_account_file):
    """Obtain an access token using a service account file."""
    credentials = service_account.Credentials.from_service_account_file(
        service_account_file,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(Request())
    return credentials.token

def synthesize_text_with_timepoints(text, service_account_file):
    # Obtain an access token
    token = obtain_access_token(service_account_file)

    # API endpoint
    url = "https://texttospeech.googleapis.com/v1beta1/text:synthesize"

    # Process the text to include marks for each word
    ssml_text = insert_marks(text)
    print("____ssml_text:"+ssml_text)

    # Prepare the payload
    payload = {
    "input": {"ssml": ssml_text},
    "voice": {
        "languageCode": "en-UK",       # Set the language to Japanese
        "name": "en-GB-Standard-A",    # Specify the voice name
        "ssmlGender": "NEUTRAL",       # Keep the gender as NEUTRAL or adjust if needed
    },
    "audioConfig": {"audioEncoding": "MP3", "pitch": 8, "speakingRate": 1.1},
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
        print(f"Error: {response.status_code}")
        print(response.text)
        return None, None, None

# For using the mapping:
def phoneme_to_image(phoneme):
    return "static/lip_shapes/" + PHONEME_TO_IMAGE_MAPPING.get(phoneme, 'TS.png')

def get_tts_and_info(text):
    SERVICE_ACCOUNT_FILE = "service-account.json"
    audio_content, timepoints, ssml_text = synthesize_text_with_timepoints(text, SERVICE_ACCOUNT_FILE)
    audio_file = f"static/{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
    with open(audio_file, "wb") as f:
        f.write(audio_content)
    print("____Timepoints:"+str(timepoints))
    print("____range:"+str(range(len(timepoints)-1)))
    #print the audio duration in seconds
    audio_dur = get_audio_duration(audio_content)-0.8
    print("___dur:"+str())
    #for some reason, the timepoints don't properly end when the audio ends. Do combat this, we will calculate a multiplier based on the duration/last timepoint. This multiplier will be used to multiply the start and end time of each lip shape.
    #multiplier = audio_dur/timepoints[-1][1]
    multiplier = audio_dur/timepoints[-1][1]
    print("___multiplier:"+str(multiplier))

    return audio_file, timepoints, audio_dur, multiplier, ssml_text

#turn this into a function
##each timepoint represents a mark in the ssml_text. Get the word in each mark, and convert it to phonemes. Get the lip shape image for each phoneme. Given the start and end time of each mark, create a map of lip shapes where the start and end time of each lip shape is the start and end time of the mark divided by the number of phonemes in the word.
def get_phonemes_and_mouth_shapes(timepoints, text, audio_dur, multiplier):
    timing_offset = 0
    phonemes = []
    for i in range(len(timepoints)):
        next_end = None
        #if we;re at the last timepoint, set the end time to the end of the audio
        if i == len(timepoints)-1:
            next_end = audio_dur
        else:
            next_end = timepoints[i+1][1]

        start_time = (timepoints[i][1]*multiplier) + timing_offset
        end_time = (next_end*multiplier) + timing_offset
        #make sure the start time is not negative
        if start_time < 0:
            start_time = 0
        if end_time < 0:
            end_time = 0.2
        
        print("word:"+str(word))
        backend = EspeakBackend('en-us')
        phn = phonemize(
            word,
            language='en-us',
            backend='espeak',
            separator=Separator(phone=None, word=' ', syllable='|'),
            strip=True,
            preserve_punctuation=True,
            njobs=4)
        word = text.split()[i]
        print("phn:"+str(phn))
        #split phonemes by grouping each pair that shows up in the mapping

        phonemes_in_word = []
        for i in range(len(phn)):
            #discard if it is a : or a space
            if phn[i] == ":" or phn[i] == " ":
                continue
            if i == len(phn)-1:
                phonemes_in_word.append(phn[i])
            else:
                if phn[i]+phn[i+1] in PHONEME_TO_IMAGE_MAPPING.keys():
                    phonemes_in_word.append(phn[i]+phn[i+1])
                else:
                    phonemes_in_word.append(phn[i])
        print("phonemes_in_word:"+str(phonemes_in_word))
        
        phoneme_duration = ((end_time - start_time)/len(phonemes_in_word))
        print(end_time - start_time)
        for j in range(len(phonemes_in_word)):
            phoneme = phonemes_in_word[j]
            phonemes.append({'phoneme':phoneme, 'start':start_time + j*phoneme_duration, 'end':start_time + (j+1)*phoneme_duration})
    return phonemes

#instead of going through each of the time points and phonemizing the associated word, lets phonemize the full text and then split it up into words that we can associate with the timepoints
def get_phoneme_words_and_mouth_shapes(timepoints, text, audio_dur, multiplier):
    mouth_shapes_and_timings = []
    backend = EspeakBackend('en-us')
    phns = phonemize(
        text,
        language='en-us',
        backend='espeak',
        separator=Separator(phone="|", word=' ', syllable=None),
        strip=True,
        preserve_punctuation=True,
        njobs=4)
    print("____phn:"+str(phns))
    #split the phonemes string into a list of phoneme words
    phoneme_words = phns.split()
    print("____phoneme_words:"+str(phoneme_words))
    #for each phoneme word, get the start and end time of the associated timepoint
    for i in range(len(timepoints)):
        next_end = None
        #if we;re at the last timepoint, set the end time to the end of the audio
        if i == len(timepoints)-1:
            next_end = audio_dur-0.05
        else:
            next_end = timepoints[i+1][1]

        start_time = (timepoints[i][1]*multiplier)
        end_time = (next_end*multiplier)
        #make sure the start time is not negative
        if start_time < 0:
            start_time = 0
        if end_time < 0:
            end_time = 0.1
        #get the phoneme word associated with this timepoint
        try:
            phoneme_word = phoneme_words[i]
            #split the phoneme word into a list of phonemes
            phonemes_in_word = phoneme_word.split("|")
            print("____phonemes_in_word:"+str(phonemes_in_word))
            phoneme_duration = (end_time - start_time)/len(phonemes_in_word)
            print(end_time - start_time)
            for j in range(len(phonemes_in_word)):
                phoneme = phonemes_in_word[j]
                #convert phoneme to mouth shape
                phoneme_image = phoneme_to_image(phoneme)
                mouth_shapes_and_timings.append((phoneme_image, start_time + j*phoneme_duration, start_time + (j+1)*phoneme_duration))
        except:
            print("mismatch between phoneme words and timepoints")
            #print the length of each
            print("phoneme_words has a length of "+str(len(phoneme_words)))
            print("timepoints has a length of "+str(len(timepoints)))
    return mouth_shapes_and_timings

@app.route('/', methods=['GET', 'POST'])
def index():
    overall_runtime = time.time()

    if request.method == 'POST':
        og_text = request.form['text']
        code_segment_runtime = time.time()
        text = get_openai_response(og_text)
        print("___get_openai_response--time:"+str(time.time()-code_segment_runtime))
        text = Punctuation(';:,.!"?()-').remove(text)
        code_segment_runtime = time.time()
        audio_file, timepoints, audio_dur, multiplier, ssml_text = get_tts_and_info(text)
        print("___get_tts_and_info--time:"+str(time.time()-code_segment_runtime))
        code_segment_runtime = time.time()
        phoneme_words = get_phoneme_words_and_mouth_shapes(timepoints, text, audio_dur, multiplier)
        print("___get_phoneme_words_and_mouth_shapes--time:"+str(time.time()-code_segment_runtime))
        print("____phoneme_words:"+str(phoneme_words))
        return render_template('index.html', audio_file=audio_file, combined=phoneme_words)
    print("___overall_runtime:"+str(time.time()-overall_runtime))
    return render_template('index.html')


def get_openai_response(text):
    #using openai ChatCompletions api
    system_prompt = "The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly."
    #format like openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Hello world"}])
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[ {"role": "system", "content": system_prompt},{"role": "user", "content": text}]
    )
    return response.choices[0].message.content
if __name__ == '__main__':
    app.run(debug=True)
