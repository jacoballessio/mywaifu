from bark import SAMPLE_RATE, generate_audio, preload_models
from scipy.io.wavfile import write as write_wav
from IPython.display import Audio

# download and load all models
preload_models()

while True:
    text_prompt = input("Enter text prompt: ")
    if text_prompt == "quit":
        break
    audio_array = generate_audio(text_prompt)
    write_wav("bark_generation.wav", SAMPLE_RATE, audio_array)
    #Audio(audio_array, rate=SAMPLE_RATE)