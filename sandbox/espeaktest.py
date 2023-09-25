from phonemizer.backend import EspeakBackend
from phonemizer.punctuation import Punctuation
from phonemizer.separator import Separator

# remove all the punctuation from the text, considering only the specified
# punctuation marks
text = "Hello, world, fuck you!"
text = Punctuation(';:,.!"?()-').remove(text)

# build the set of all the words in the text
words = {w.lower() for line in text for w in line.strip().split(' ') if w}

# initialize the espeak backend for English
backend = EspeakBackend('en-us')

# separate phones by a space and ignoring words boundaries
separator = Separator(phone=' ', word=None)

#track the time it takes to phonemize the text

import time
start_time = time.time()

# build the lexicon by phonemizing each word one by one. The backend.phonemize
# function expect a list as input and outputs a list.
lexicon = {
    word: backend.phonemize([word], separator=separator, strip=True)[0]
    for word in words}

print("--- %s seconds ---" % (time.time() - start_time))
print(lexicon)
import subprocess

def text_to_speech(text, output_file=None):
    command = ['espeak']
    if output_file:
        command.extend(['-w', output_file])
    command.append(text)
    print(command)
    subprocess.run(command)
    
text_to_speech(text)
