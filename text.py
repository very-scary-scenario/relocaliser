def sanitise(text):
    return (text.replace('“', '"')
            .replace('”', '"')
            .replace("‘", "'")
            .replace("’", "'")
            .replace('...', '…')
            .lower()
            .replace('é', 'e'))
