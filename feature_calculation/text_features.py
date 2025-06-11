try:
    from feature_calculation import transcription_functions
except:
    import transcription_functions
import nltk
import re
import numpy as np
# nltk.download('punkt_tab')
# nltk.download('averaged_perceptron_tagger_eng')
def avg_word_length(string):
    words = string.split()
    return sum(len(word) for word in words) / len(words) if len(words) > 0 else 0
def avg_syllables_per_word(string):
    words = string.split()
    return sum(transcription_functions.count_syllables(word) for word in words) / len(words) if len(words) > 0 else 0
def content_richness(string):
    '''
    Content Richness: Measures the ratio of open class to closed class words in a given string.
    '''
    text = nltk.word_tokenize(string)
    tag_dict = nltk.pos_tag(text)
    open_class_tags = {"NNS", "NN", "NNP", "NNPS", "VB", "VBD", "VBG", "VBN", "VBP", "VBZ", "JJ", "JJR", "JJS", "RB", "RBR", "RBS", "UH"}
    closed_class_tags = {"CC", "CD", "DT","PDT","WDT", "EX", "FW", "IN", "PRP", "PRP$", "WP", "WP$", "TO", "POS"}
    opens = 0
    closed = 0
    for token in tag_dict:
        try:
            if token[1] in open_class_tags:
                opens += 1
            elif token[1] in closed_class_tags:
                closed += 1
        except:
            continue
    return opens / (opens + closed) if opens + closed > 0 else 0
# TODO: Is eyeballing window_size okay?
def mattr(string, window_size = 8):
    '''
    MATTR: Measures the number of unique words in a given window of words.
    '''
    words = string.split()
    window_vals = []
    end = window_size
    window = words[:end]
    viewed_words = {}
    for word in window:
        viewed_words[word] = 1 if word not in viewed_words else viewed_words[word] + 1
    while end < len(words):
        count = len(viewed_words)/window_size
        window_vals.append(count)
        viewed_words[window[0]] -= 1
        if viewed_words[window[0]] == 0:
            del viewed_words[window[0]]
        window.pop(0)
        window.append(words[end])
        viewed_words[words[end]] = 1 if words[end] not in viewed_words else viewed_words[words[end]] + 1
        end += 1
    return np.mean(window_vals)
def n_grams(string, n = 2):
    '''
    N-Grams: Measures the number of repeated n-grams in a given string.
    '''
    words = string.split()
    n_grams = [x for x in nltk.ngrams(words, n)]
    n_gram_set = set(n_grams)
    repeats = len(n_grams) - len(n_gram_set)
    return repeats
def phrase_patterns(string):
    '''
    Phrase Patterns: Measures the number of repeated n-grams in a given string.
    '''
    result = 0
    for i in range(2, 5):
        result += n_grams(string, i)
    return result
def sentence_length(string):
    '''
    Sentence Length: Measures the average number of words per sentence
    '''
    sentences = nltk.sent_tokenize(string)
    return np.mean([len(sentence.split()) for sentence in sentences])

def calculate_text_features(text_path):
    with open(text_path, 'r') as f:
        text = f.read()
    text = text.lower()
    return {
        "avg_word_length": avg_word_length(text),
        "avg_syllables_per_word": avg_syllables_per_word(text),
        "content_richness": content_richness(text),
        "mattr": mattr(text),
        "phrase_patterns": phrase_patterns(text),
        "sentence_length": sentence_length(text)
    }

    
if __name__ == "__main__":
    text_path = "/Users/thomas.cong/Downloads/ResearchCode/Text Files/71223-05-01-2025_21_08_43_preprocessed.txt"
    print(calculate_text_features(text_path))
    
    