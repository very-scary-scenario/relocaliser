def normalise(text):
    return (text.replace('“', '"')
            .replace('”', '"')
            .replace("‘", "'")
            .replace("’", "'")
            .replace('...', '…')
            .lower()
            .replace('é', 'e'))


def ignore_word_order(text):
    return ' '.join(sorted(text.split(' ')))
