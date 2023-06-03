from string import whitespace
import nltk


def preprocess(text, mystem, stop_words):
    text = text.lower()

    tokens = nltk.word_tokenize(text, language='russian')  # разбили на токены

    russian_unicode = list(range(1040, 1104)) + [1025, 1105]

    _tokens = []
    for token in tokens:  # убрали англоязычные слова
        i = 0
        for chr in token:
            if ord(chr) in russian_unicode:
                i += 1
        if i == len(token):
            _tokens.append(token)

    tokens = [token for token in _tokens if token not in stop_words]  # убрали русскоязычные стоп слова

    tokens = [token for token in tokens if 3 < len(token) < 12]  # убрали длинные и короткие слова

    str_tokens = ' '.join(token for token in tokens)
    tokens = mystem.lemmatize(str_tokens)  # лемматизировали

    return [token for token in tokens if token not in whitespace]