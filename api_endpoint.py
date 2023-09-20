#flask app that will be used to create the api endpoint
#will take in text or an audio file.
#Will return LLM text response, phoneme mappings and timings, and TTS audio of the LLM response.

from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask_cors import CORS
import os
import json
from werkzeug.utils import secure_filename
from llama2_gen2 import llama2_gen_thread as LLM
from tts_phonemes import *
from flask import send_file
from flask import send_from_directory
import io
import base64
import numpy as np



app = Flask(__name__, static_folder='build')
CORS(app)
api = Api(app)

#lets create a boilerplate for the api endpoint
class LLM_API(Resource):
    def get(self):
        return {'hello': 'world'}

    def post(self):
        #get the data from the request
        data = request.get_json()
        print(data)
        #get the text from the data
        user_text = data['text']
        #create an instance of the LLM class
        #get the LLM response
        llm_response = LLM(user_text)
        print("__ll"+llm_response)
        #remove emojis
        cleaned_text = llm_response.encode('ascii', 'ignore').decode('ascii')
        
        if cleaned_text.isspace() or cleaned_text == "" or cleaned_text == None:
            cleaned_text = "Beeeeeep. Not sure how to pronounce that."
        #get the phoneme mappings and timings
        audio_file, timepoints, audio_dur, multiplier, ssml_text = get_tts_and_info(cleaned_text)
        phoneme_mappings = get_phoneme_words_and_mouth_shapes(timepoints, cleaned_text, audio_dur, multiplier)
        #return the LLM response, phoneme mappings, and TTS audio
        return {'llm_response': llm_response, 'phoneme_mappings': phoneme_mappings, 'tts_audio': audio_file}

#setup email endpoint to store emails
class Email_API(Resource):
    def get(self):
        return {'hello': 'world'}

    def post(self):
        #get the data from the request
        data = request.get_json()
        print(data)
        #get the email from the data
        user_email = data['email']
        #store the email
        with open('emails.txt', 'a') as f:
            f.write(user_email + '\n')
        #return the email
        return {'email': user_email}

api.add_resource(Email_API, '/email')
#add the api endpoint to the api
api.add_resource(LLM_API, '/llm')

#serve front_end_react_build at /
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and path.endswith('.js'):
        return send_from_directory('build/static/js', path)
    if path != "" and path.endswith('.css'):
        return send_from_directory('build/static/css', path)
    return send_from_directory('build', 'index.html')


#run the app
if __name__ == '__main__':
    app.run(debug=True)
