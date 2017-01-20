from datetime import datetime, timedelta
import html
import os

from camel import Camel
import tweepy

from game import Game, camel_registry
import keys


auth = tweepy.OAuthHandler(keys.consumer_key, keys.consumer_secret)
auth.set_access_token(keys.access_token, keys.access_token_secret)
api = tweepy.API(auth)

handle = auth.get_username()

GAMES_DIR = os.path.join(os.path.dirname(__file__), 'games')
if not os.path.isdir(GAMES_DIR):
    os.mkdir(GAMES_DIR)

camel = Camel([camel_registry])


class TwitterGame(tweepy.StreamListener):
    def __init__(
        self, api, game, initial_status_id, trigger_status_ids=None,
        end_at=None, over=False,
    ):
        self.game = game
        self.initial_status_id = initial_status_id
        self.trigger_status_ids = [initial_status_id]

        if end_at is None:
            end_at = datetime.now() + timedelta(hours=1)

        self.end_at = end_at
        self.over = over
        self.save()
        return super().__init__(api)

    def save(self):
        with open(os.path.join(GAMES_DIR, self.end_at.isoformat()), 'w') as sf:
            sf.write(camel.dump(self))

    def handle_play(self, status):
        if not status.text.startswith('@{}'.format(handle)):
            # ignore things that aren't mentions
            return

        if status.in_reply_to_status_id not in self.trigger_status_ids:
            # ignore things that aren't replies to the game in progress
            return

        self.trigger_status_ids.append(status.id)

        text = html.unescape(status.text)
        entry = text.replace('@{}'.format(handle), '').strip()
        score = self.game.play(entry)

        if score == 1:
            # correct! end the game
            api.update_status(
                "@{} Correct! I'll start a new game soon.".format(
                    status.author.screen_name, score,
                ),
                n_reply_to_status_id=status.id,
            )
            api.retweet(status.id)
            self.over = True

            return False
        else:
            # provide feeback
            self.trigger_status_ids.append(api.update_status(
                "@{} That's {:.1%} right.".format(
                    status.author.screen_name, score,
                ),
                in_reply_to_status_id=status.id,
            ).id)

    def on_status(self, status):
        rv = self.handle_play(status)

        if rv is False:
            # there's no need to force the game to end; it's already over
            self.save()
            return rv

        elif datetime.now() > self.end_at:
            api.update_status(
                'Game over. The answer was {}.'.format(self.game.original),
                in_reply_to_status_id=self.initial_status_id,
            )
            self.over = True
            self.save()
            return False

        else:
            self.save()
            return rv

    def on_connect(self):
        mentions = api.mentions_timeline(since_id=self.trigger_status_ids[-1])
        for status in sorted(mentions, key=lambda s: s.created_at):
            if self.on_status(status) is False:
                raise ValueError('this game ended while we were away')


def start_new_game():
    game = Game()
    listener = TwitterGame(api, game, api.update_status(game.clue).id)
    return listener


def run_game():
    saved_games = sorted(
        (fn for fn in os.listdir(GAMES_DIR) if not fn.startswith('.'))
    )

    if not saved_games:
        listener = start_new_game()
    else:
        with open(os.path.join(GAMES_DIR, saved_games[-1])) as gf:
            listener = camel.load(gf.read())
        if listener.over:
            listener = start_new_game()

    stream = tweepy.Stream(auth=api.auth, listener=listener)
    stream.userstream()


@camel_registry.dumper(TwitterGame, 'twitter_game', version=1)
def _dump_twitter_game(tg):
    return {
        a: getattr(tg, a) for a in [
            'game', 'initial_status_id', 'trigger_status_ids', 'end_at',
            'over',
        ]
    }


@camel_registry.loader('twitter_game', version=1)
def _load_twitter_game(data, version):
    return TwitterGame(api=api, **data)


if __name__ == '__main__':
    run_game()
