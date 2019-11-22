import nltk

module_path = [('punkt', 'tokenizers/punkt'), ('words', 'corpora/words'), ('wordnet', 'corpora/wordnet'),
               ('averaged_perceptron_tagger', 'taggers/averaged_perceptron_tagger')]

for module, path in module_path:
    try:
        nltk.data.find(path)
    except LookupError:
        nltk.download(module)
