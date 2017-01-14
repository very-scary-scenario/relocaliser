from datetime import datetime, timedelta
import html

import tweepy

from game import Game
import keys


auth = tweepy.OAuthHandler(keys.consumer_key, keys.consumer_secret)
auth.set_access_token(keys.access_token, keys.access_token_secret)
api = tweepy.API(auth)

handle = auth.get_username()


class TwitterGame(tweepy.StreamListener):
    def __init__(self, api, game, initial_status_id):
        self.game = game
        self.initial_status_id = initial_status_id
        self.trigger_status_ids = {initial_status_id}
        self.end_at = datetime.now() + timedelta(hours=1)
        return super().__init__(api)

    def handle_play(self, status):
        if not status.text.startswith('@{}'.format(handle)):
            # ignore things that aren't mentions
            return

        if status.in_reply_to_status_id not in self.trigger_status_ids:
            # ignore things that aren't replies to the game in progress
            return

        self.trigger_status_ids.add(status.id)

        text = html.unescape(status.text)
        entry = text.replace('@{}'.format(handle), '').strip()
        score = self.game.play(entry)

        if score == 1:
            # correct! end the game
            api.update_status(
                "@{} Correct! I'll start a new game soon.".format(
                    status.author.screen_name, score,
                ),
                in_reply_to_status_id=status.id,
            )
            api.retweet(status.id)

            return False
        else:
            # provide feeback
            self.trigger_status_ids.add(api.update_status(
                "@{} That's {:.1%} right.".format(
                    status.author.screen_name, score,
                ),
                in_reply_to_status_id=status.id,
            ).id)

    def on_status(self, status):
        rv = self.handle_play(status)

        if rv is False:
            # there's no need to force the game to end; it's already over
            return rv

        elif datetime.now() > self.end_at:
            api.update_status(
                'Game over. The answer was {}'.format(self.game.original),
                in_reply_to_status_id=self.initial_status_id,
            )
            return False

        else:
            return rv


def run_game():
    game = Game()
    listener = TwitterGame(api, game, api.update_status(game.clue).id)
    stream = tweepy.Stream(auth=api.auth, listener=listener)
    stream.userstream()


if __name__ == '__main__':
    run_game()
