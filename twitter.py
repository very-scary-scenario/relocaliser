import tweepy

from game import Game
import keys


auth = tweepy.OAuthHandler(keys.consumer_key, keys.consumer_secret)
auth.set_access_token(keys.access_token, keys.access_token_secret)
api = tweepy.API(auth)

handle = auth.get_username()


class TwitterGame(tweepy.StreamListener):
    def __init__(self, api, game, trigger_status_id):
        self.game = game
        self.trigger_status_ids = {trigger_status_id}
        return super().__init__(api)

    def on_status(self, status):
        if not status.text.startswith('@{}'.format(handle)):
            # ignore things that aren't mentions
            return

        if status.in_reply_to_status_id not in self.trigger_status_ids:
            # ignore things that aren't replies to the game in progress
            return

        text = status.text
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


def run_game():
    game = Game()
    listener = TwitterGame(api, game, api.update_status(game.clue).id)
    stream = tweepy.Stream(auth=api.auth, listener=listener)
    stream.userstream()


if __name__ == '__main__':
    while True:
        run_game()
