import random

from bs4 import BeautifulSoup
import requests

import keys


LIMIT = 100


def giantbomb(method, **params):
    resp = requests.get(
        'https://www.giantbomb.com/api/{}/'.format(method),
        params={
            'format': 'json',
            'limit': LIMIT,
            'sort': 'id:asc',
            'api_key': keys.giantbomb,
            **params,
        },
        headers={
            'user-agent': 'unshuffle-source-giantbomb/0.0',
        },
    )
    resp.raise_for_status()
    return resp.json()


def _get_name():
    seen_ids = set()
    total = giantbomb('games')['number_of_total_results']

    games = giantbomb(
        'games',
        offset=random.randrange(0, total-LIMIT)
    )['results']
    random.shuffle(games)

    for game in games:
        if (
            game['id'] in seen_ids or
            not game.get('name') or

            # and now we have to attempt to filter out games that nobody
            # has heard of
            len(BeautifulSoup(
                game['description'] or '', 'lxml'
            ).get_text()) < 1000
        ):
            continue

        name = game['name']

        while '  ' in name:
            name = name.replace('  ', ' ')

        return name


def get_name():
    while True:
        name = _get_name()
        if name:
            return name
