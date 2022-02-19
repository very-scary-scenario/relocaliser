def normalise(text: str) -> str:
    return (text.replace('“', '"')
            .replace('”', '"')
            .replace("‘", "'")
            .replace("’", "'")
            .replace('...', '…')
            .lower()
            .replace('é', 'e'))


def ignore_word_order(text: str) -> str:
    return ' '.join(sorted(text.split(' ')))
