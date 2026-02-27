# bot/poster.py
import tweepy
import os
import time
from dotenv import load_dotenv

load_dotenv()


def get_client():
    return tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
        wait_on_rate_limit=True,
    )


def post_tweet_thread(tweets: list, image_path: str = None) -> bool:
    client = get_client()
    previous_id = None

    for i, tweet_text in enumerate(tweets):
        # Trim to 280 chars just in case
        tweet_text = tweet_text[:280]
        try:
            if previous_id:
                resp = client.create_tweet(
                    text=tweet_text,
                    in_reply_to_tweet_id=previous_id
                )
            else:
                resp = client.create_tweet(text=tweet_text)

            previous_id = resp.data["id"]
            print(f"[POSTER] ✅ Tweet {i+1} posted! ID: {previous_id}")
            time.sleep(3)

        except tweepy.TweepyException as e:
            print(f"[POSTER] ❌ Failed tweet {i+1}: {e}")
            if i == 0:
                return False
            break

    return True
