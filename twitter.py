from datetime import datetime, timedelta
import html
import os

from camel import Camel
import tweepy

from game import Game, camel_registry
import keys

from languages import languages
from image import generate_image

auth = tweepy.OAuthHandler(keys.consumer_key, keys.consumer_secret)
auth.set_access_token(keys.access_token, keys.access_token_secret)
api = tweepy.API(auth)

handle = auth.get_username()

GAMES_DIR = os.path.join(os.path.dirname(__file__), 'games')
if not os.path.isdir(GAMES_DIR):
    os.mkdir(GAMES_DIR)

IMAGES_DIR = os.path.join(os.path.dirname(__file__), 'images')
if not os.path.isdir(IMAGES_DIR):
    os.mkdir(IMAGES_DIR)

camel = Camel([camel_registry])


class TwitterGame:
    def __init__(
        self, api, game, initial_status_id, trigger_status_ids=None,
        end_at=None, over=False,
    ):
        self.game = game
        self.initial_status_id = initial_status_id
        self.trigger_status_ids = [initial_status_id]

        if end_at is None:
            end_at = datetime.now() + timedelta(hours=3)

        self.end_at = end_at
        self.over = over
        self.save()

    def __str__(self):
        return str(self.game)

    def save(self):
        with open(os.path.join(GAMES_DIR, self.end_at.isoformat()), 'w') as sf:
            sf.write(camel.dump(self))

    def get_alt_text(self):
        # Make best effort to include all information within 420 characters
        alt_text = " » ".join("{}: {}".format(
            languages[step[0]], step[-1]) for step in self.game.steps)
        if len(alt_text) <= 420:
            return alt_text

        alt_text = " » ".join("{}: {}".format(
            step[0], step[-1]) for step in self.game.steps)

        if len(alt_text) <= 420:
            return alt_text

        return alt_text[:419] + "…"

    def tweet_image(self, status, *args, **kwargs):
        image_path = os.path.join(IMAGES_DIR,
                                  "{}.png".format(self.end_at.isoformat()))
        generate_image(self.game.steps, image_path)

        # https://github.com/tweepy/tweepy/issues/643
        upload = api.media_upload(filename=image_path)
        media_ids = [upload.media_id_string]

        # http://github.com/tweepy/tweepy/pull/727/commits/b387331c174a451cb8dba44b4e0c7988a92bad1b
        # Could we subclass API and implement this pull request ourselves?
        post_data = {
            "media_id": media_ids[0],
            "alt_text": {
                "text": self.get_alt_text()
            }
        }
        json = tweepy.utils.import_simplejson()
        tweepy.binder.bind_api(api=api,
                               path='/media/metadata/create.json',
                               method='POST',
                               allowed_param=[],
                               require_auth=True,
                               upload_api=True
                               )(post_data=json.dumps(post_data))

        api.update_status(media_ids=media_ids,
                          status=status,
                          *args, **kwargs)

    def handle_play(self, status):
        if not status.text.startswith('@{}'.format(handle)):
            # ignore things that aren't mentions
            return

        if status.in_reply_to_status_id not in self.trigger_status_ids:
            # ignore things that aren't replies to the game in progress
            return

        if status.id in self.trigger_status_ids:
            # ignore things we've already responded to
            return

        self.trigger_status_ids.append(status.id)

        text = html.unescape(status.text)
        entry = text.replace('@{}'.format(handle), '').strip()
        score = self.game.play(entry)

        if score == 1:
            # correct! end the game
            api.retweet(status.id)
            self.tweet_image(
                "Well done @{}! I'll start a new game soon.".format(
                    status.author.screen_name,
                ),
                in_reply_to_status_id=status.id,
            )
            self.over = True

            return False
        else:
            # provide feeback
            try:
                self.trigger_status_ids.append(api.update_status(
                    "@{} That's {:.1%} right.".format(
                        status.author.screen_name, score,
                    ),
                    in_reply_to_status_id=status.id,
                ).id)
            except tweepy.TweepError as e:
                print(e)

    def on_status(self, status):
        rv = self.handle_play(status)

        if rv is False:
            # there's no need to force the game to end; it's already over
            self.save()
            print('game already over')
            return rv

        else:
            self.save()
            print('not from this game?')
            return rv

    def on_load(self):
        if datetime.now() > self.end_at:
            self.tweet_image(
                'Game over. The answer was {}.'.format(self.game.original),
                in_reply_to_status_id=self.initial_status_id,
            )
            self.over = True
            self.save()
            return False

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

    listener.on_load()


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
    rv = TwitterGame(api=api, **data)
    print('loaded {}'.format(rv))
    return rv


if __name__ == '__main__':
    run_game()
