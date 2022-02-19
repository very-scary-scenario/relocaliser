import random
from Levenshtein import ratio
from typing import List, Tuple

from giantbomb import get_name
from argostranslate.translate import Language, get_installed_languages
from text import ignore_word_order


ENGLISH: Language = [lang for lang in get_installed_languages() if lang.code == 'en'][0]


def get_directions() -> List[Tuple[Language, Language]]:
    return [
        (source, destination)
        for source in get_installed_languages()
        for destination in get_installed_languages()
    ]


def build_route(step_count: int, source: Language, target: Language) -> List[Tuple[Language, Language]]:
    """
    Build a random route through the translator with as many steps as
    requested, starting at `source` and ending at `target`
    """

    directions = get_directions()
    current_lang = source
    route: List[Tuple[Language, Language]] = []

    while not route:
        for n in range(step_count):
            options = [
                d for d in directions
                if current_lang.code == d[0].code
            ]

            if n == (step_count - 1):
                # this is the last step, we need to get to our target
                options = [
                    o for o in options
                    if o[-1].code == target.code
                ]

            if not options:
                route = []
                break

            route.append(random.choice(options))
            current_lang = route[-1][-1]

    return route


def party(phrase: str, step_count: int, source: Language, target: Language) -> List[Tuple[Language, str]]:
    route = build_route(step_count, source, target)
    steps = [(source, phrase)]

    for source_language, destination_language in route:
        translation = source_language.get_translation(destination_language)
        steps.append((destination_language, translation.translate(steps[-1][-1])))

    return steps


def interesting_party(
    step_count: int = 8, source: Language = ENGLISH, target: Language = ENGLISH,
) -> List[Tuple[Language, str]]:
    while True:
        while True:
            phrase = get_name()
            if len(phrase) < 100:
                break

        steps = party(phrase, step_count, source, target)
        result = steps[-1][-1]

        # we do this both in and out of order so that cases where spaces are
        # removed or replaced don't cause the false assertion that a party is
        # interesting, but we have different targets because word order changes
        # often *are* interesting, but only if at least something else has
        # changed
        #
        # case in point, in testing while not doing this, the translation of
        # 'Pandemic Express' to 'Pandemic-Express' was returned as an
        # interesting party, when it obviously isn't
        #
        # the specific numbers here may need to be calibrated over time; i only
        # sampled about fifty parties with this configuration

        if (
            ratio(phrase.lower(), result.lower()) < 0.7
        ) and (
            ratio(
                ignore_word_order(phrase.lower()),
                ignore_word_order(result.lower()),
            ) < 0.9
        ):
            return steps


if __name__ == '__main__':
    print('\n'.join(f'{lang.code}: {phrase}' for lang, phrase in interesting_party()))
