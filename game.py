import signal

from camel import CamelRegistry
from Levenshtein import ratio

from party import interesting_party
from text import normalise


camel_registry = CamelRegistry()


class Game:
    def __init__(self, steps=None):
        if steps is None:
            self.steps = interesting_party()
        else:
            self.steps = steps

        self.original = self.steps[0][-1]
        self.clue = self.steps[-1][-1]

    def play(self, guess):
        return ratio(normalise(guess), normalise(self.original))


@camel_registry.dumper(Game, 'game', version=1)
def _dump_game(game):
    return {'steps': game.steps}


@camel_registry.loader('game', version=1)
def _load_game(data, version):
    return Game(**data)


if __name__ == '__main__':
    import sys

    game = Game()

    def give_up(s, f):
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
