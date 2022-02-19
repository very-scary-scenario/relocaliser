import signal

from camel import CamelRegistry
from Levenshtein import ratio
from types import FrameType
from typing import List, NoReturn, Optional, Tuple

from argostranslate.translate import Language
from party import interesting_party
from text import normalise


camel_registry = CamelRegistry()


class Game:
    def __init__(self, steps: List[Tuple[Language, str]] = None) -> None:
        if steps is None:
            self.steps = interesting_party()
        else:
            self.steps = steps

        self.original = self.steps[0][-1]
        self.clue = self.steps[-1][-1]

    def __str__(self) -> str:
        return self.clue

    def play(self, guess: str) -> float:
        return ratio(normalise(guess), normalise(self.original))


@camel_registry.dumper(Game, 'game', version=1)
def _dump_game(game: Game) -> dict:
    return {'steps': game.steps}


@camel_registry.loader('game', version=1)
def _load_game(data: dict, version: int) -> Game:
    return Game(**data)


if __name__ == '__main__':
    import sys

    game = Game()

    def give_up(s: int, f: Optional[FrameType]) -> NoReturn:
        print('\nyou gave up\nthe answer was: {}'.format(game.original))
        sys.exit(1)

    signal.signal(signal.SIGINT, give_up)

    print(game.clue)
    while True:
        score = game.play(input('guess: '))
        if score == 1:
            print('correct')
            break
        else:
            print('incorrect; closeness: {:.1%}'.format(score))
