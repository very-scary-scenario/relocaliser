import random
import requests

from keys import yandex_translate


def _api(method, **params):
    return requests.get(
        'https://translate.yandex.net/api/v1.5/tr.json/{}'
        .format(method),
        params={
            'key': yandex_translate,
            **params,
        }
    ).json()


def get_directions():
    return list(
        tuple(r.split('-'))
        for r in _api('getLangs')['dirs']
    )


def translate(text, direction):
    resp, = _api('translate', text=text, lang='-'.join(direction))['text']
    return resp


def build_route(steps=5, source='en', target='en'):
    """
    Build a random route through the translator with as many steps as
    requested, starting at `source` and ending at `target`
    """

    directions = get_directions()
    current_lang = source
    route = []

    while not route:
        for n in range(steps):
            options = [
                d for d in directions
                if current_lang == d[0]
            ]

            if n == (steps - 1):
                # this is the last step, we need to get to our target
                options = [
                    o for o in options
                    if o[-1] == target
                ]

            if not options:
                route = []
                break

            route.append(random.choice(options))
            current_lang = route[-1][-1]

    return route


def party(phrase, source='en', **params):
    route = build_route(source=source, **params)
    steps = [(source, phrase)]

    for direction in route:
        steps.append((direction[-1], translate(
            text=steps[-1][-1],
            direction=direction,
        )))

    return steps


if __name__ == '__main__':
    import sys
    phrase = ' '.join(sys.argv[1:])

    print('\n'.join(' '.join(i) for i in party(phrase)))
