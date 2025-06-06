from . import transcription_functions
def avg_word_length(text_path):
    with open(text_path, 'r') as f:
        text = f.read()
    words = text.split()
    return sum(len(word) for word in words) / len(words) if len(words) > 0 else 0

def avg_syllables_per_word(text_path):
    with open(text_path, 'r') as f:
        text = f.read()
    words = text.split()
    return sum(transcription_functions.count_syllables(word) for word in words) / len(words) if len(words) > 0 else 0
        
    