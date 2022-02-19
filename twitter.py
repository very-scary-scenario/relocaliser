from datetime import datetime, timedelta
import html
import os
from typing import List

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

ID_TYPE = str  # tweet IDs are now strings, i think? i should check.

camel = Camel([camel_registry])


class TwitterGame:
    def __init__(
        self, api: tweepy.API, game: Game, initial_status_id: ID_TYPE, trigger_status_ids: List[ID_TYPE] = None,
        end_at: datetime = None, over: bool = False, seen_statuses: List[ID_TYPE] = None,
    ) -> None:
        self.game = game
        self.initial_status_id = initial_status_id
        self.trigger_status_ids = trigger_status_ids or [initial_status_id]
        self.seen_statuses = seen_statuses or []

        if end_at is None:
            end_at = datetime.now() + timedelta(hours=8)

        self.end_at = end_at
        self.over = over
        self.save()

    def __str__(self) -> str:
        return str(self.game)

    def save(self) -> None:
        with open(os.path.join(GAMES_DIR, self.end_at.isoformat()), 'w') as sf:
            sf.write(camel.dump(self))

    def get_alt_text(self) -> str:
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

    def tweet_image(self, status: str, in_reply_to_status_id: ID_TYPE = None) -> None:
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

        api.update_status(media_ids=media_ids, status=status, in_reply_to_status_id=in_reply_to_status_id)

    def handle_play(self, status: tweepy.Status) -> bool:
        if not status.text.startswith('@{}'.format(handle)):
            # ignore things that aren't mentions
            return True

        if status.in_reply_to_status_id not in self.trigger_status_ids:
            # ignore things that aren't replies to the game in progress
            return True

        if status.id in self.trigger_status_ids:
            # ignore things we've already responded to
            return True

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
            return True

    def on_status(self, status: tweepy.Status) -> bool:
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

    def on_load(self) -> bool:
        if datetime.now() > self.end_at:
            self.tweet_image(
                "Time's up. The answer was {}.".format(self.game.original),
                in_reply_to_status_id=self.initial_status_id,
            )
            self.over = True
            self.save()
            return False

        mentions = api.mentions_timeline(since_id=self.trigger_status_ids[-1])
        for status in sorted(mentions, key=lambda s: s.created_at):
            if status.id in self.seen_statuses:
                continue

            if self.on_status(status) is False:
                raise ValueError('this game ended while we were away')

            self.seen_statuses.append(status.id)
            self.save()

        return True


def start_new_game() -> TwitterGame:
    game = Game()
    listener = TwitterGame(api, game, api.update_status(game.clue).id)
    return listener


def run_game() -> None:
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
def _dump_twitter_game(tg: TwitterGame) -> dict:
    return {
        a: getattr(tg, a) for a in [
            'game', 'initial_status_id', 'trigger_status_ids', 'seen_statuses',
            'end_at', 'over',
        ]
    }


@camel_registry.loader('twitter_game', version=1)
def _load_twitter_game(data: dict, version: int) -> TwitterGame:
    rv = TwitterGame(api=api, **data)
    print('loaded {}'.format(rv))
    return rv


if __name__ == '__main__':
    run_game()
