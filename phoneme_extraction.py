import parselmouth
from parselmouth.praat import call

def extract_phonemes(audio_path):
    sound = parselmouth.Sound(audio_path)
    manipulation = call(sound, "To Manipulation", 0.01, 75, 600)
    
    # Auto annotate phonemes
    textgrid = call(manipulation, "To TextGrid (silences)", "Mary John bell", "phoneme", 100, 0, 0.03, 0.1, 0.1, 0.05, 0.2)
    
    intervals = call(textgrid, "Get number of intervals", 1)
    phonemes = []
    for i in range(1, intervals + 1):
        label = call(textgrid, "Get label of interval", 1, i)
        if label:
            start_time = call(textgrid, "Get start time of interval", 1, i)
            end_time = call(textgrid, "Get end time of interval", 1, i)
            phonemes.append({'start': start_time, 'end': end_time, 'phoneme': label})
            
    return phonemes
