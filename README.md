# Relocaliser 3000™

An extremely difficult-to-speedrun entry to [GAMES MADE
QUICK???](https://itch.io/jam/games-made-quick).

## Playing on Twitter

When a game starts, [@relocaliser](https://twitter.com/relocaliser) posts a
recursively translated game name. You play by replying to the most recent one
of these with what you think the actual game name is. If you are correct, your
answer will be retweeted and a new game will start.

Answers are case-insensitive, but punctuation should be correct. Game names are
taken from [Giant Bomb](http://www.giantbomb.com), so if you're struggling with
what variation of the name of a game to use, consult their database.

Games end when someone gets the answer right, or when a guess is submitted more
than an hour after the clue was posted.

## Playing locally (or making your own frontend)

This is more complicated. You'll need to get [Yandex
Translate](https://tech.yandex.com/translate/) and [Giant
Bomb](http://www.giantbomb.com/api/) API keys, and put them into a `keys.py`
file alongside the other files in your local version. You should format it like
this:

```python
yandex_translate = 'your yandex translate api key'
giantbomb = 'your giant bomb api key'
```

A prototype for this file can be found in `keys.py.prototype`. (If you only want to play locally, you can ignore the Twitter-related lines.)

You'll then need to `cd` to your cloned repository and run `pip3 install -r
requirements.txt`. Then, you should be able to play the game on the command
line by running `python3 game.py`.

If you want to write another frontend, you should be able to import everything
you need from `game.py`.

## Running the twitter bot

I recommend you make sure you can play locally before you do this, but once you
have, make yourself a [Twitter app](https://apps.twitter.com) and add something
resembling the following to your `keys.py`:

```python
consumer_key = 'consumer key'
consumer_secret = 'consumer secret'
access_token = 'access token'
access_token_secret = 'access token secret'
```

Then, run `python3 twitter.py` to run a single game. On my server, I have
`while :; do python twitter.py; sleep 10; done` running in a `tmux` session, to
automatically have a new game begin after one ends.
