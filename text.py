def sanitise(text):
    return (text.replace('“', '"')
            .replace('”', '"')
            .replace("‘", "'")
            .replace("’", "'")
            .lower())
