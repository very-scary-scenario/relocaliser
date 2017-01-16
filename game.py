import signal

from Levenshtein import ratio

from party import interesting_party
from text import sanitise


class Game:
    def __init__(self):
        self.steps = interesting_party()
        self.original = self.steps[0][-1]
        self.clue = self.steps[-1][-1]

    def play(self, guess):
        return ratio(sanitise(guess), sanitise(self.original))


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
