def normalise(text):
    return (text.replace('“', '"')
            .replace('”', '"')
            .replace("‘", "'")
            .replace("’", "'")
            .replace('...', '…')
            .lower()
            .replace('é', 'e'))
