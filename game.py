from Levenshtein import ratio

from party import interesting_party


class Game:
    def __init__(self):
        self.steps = interesting_party()
        self.original = self.steps[0][-1]
        self.clue = self.steps[-1][-1]

    def play(self, guess):
        return ratio(guess.lower(), self.original.lower())


if __name__ == '__main__':
    game = Game()
    print(game.clue)
    while True:
        score = game.play(input('guess: '))
        if score == 1:
            print('correct')
            break
        else:
            print('incorrect; closeness: {}'.format(score))
