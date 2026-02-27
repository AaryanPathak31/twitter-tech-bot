# bot/poster.py
import tweepy
import os
import time
from dotenv import load_dotenv

load_dotenv()


def get_twitter_client():
    """Initialize Tweepy client with credentials from environment."""
    client = tweepy.Client(
        bearer_token=os.environ["X_BEARER_TOKEN"],
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
        wait_on_rate_limit=True,
    )
    return client


def get_twitter_api_v1():
    """
    Initialize Tweepy v1.1 API — needed ONLY for media upload.
    (Media upload still uses v1.1 endpoint even on free tier)
    """
    auth = tweepy.OAuth1UserHandler(
        os.environ["X_API_KEY"],
        os.environ["X_API_SECRET"],
        os.environ["X_ACCESS_TOKEN"],
        os.environ["X_ACCESS_TOKEN_SECRET"],
    )
    return tweepy.API(auth)


def upload_image(image_path: str) -> str | None:
    """Upload image using v1.1 API. Returns media_id string."""
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        api_v1 = get_twitter_api_v1()
        media = api_v1.media_upload(filename=image_path)
        print(f"[POSTER] Uploaded image, media_id: {media.media_id_string}")
        return media.media_id_string
    except Exception as e:
        print(f"[POSTER] Image upload failed: {e}")
        return None


def post_tweet_thread(tweets: list, image_path: str = None) -> bool:
    """
    Post a thread of tweets. Attaches image to the first tweet only.
    Returns True on success, False on failure.
    """
    client = get_twitter_client()
    previous_tweet_id = None

    for i, tweet_text in enumerate(tweets):
        # Only attach image to first tweet
        media_ids = None
        if i == 0 and image_path:
            media_id = upload_image(image_path)
            if media_id:
                media_ids = [media_id]

        try:
            if previous_tweet_id:
                # Reply to previous tweet to form thread
                response = client.create_tweet(
                    text=tweet_text,
                    in_reply_to_tweet_id=previous_tweet_id,
                    media_ids=media_ids,
                )
            else:
                response = client.create_tweet(
                    text=tweet_text,
                    media_ids=media_ids,
                )

            previous_tweet_id = response.data["id"]
            print(f"[POSTER] Tweet {i+1} posted. ID: {previous_tweet_id}")

            # Wait between thread tweets to avoid rate limits
            if i < len(tweets) - 1:
                time.sleep(3)

        except tweepy.TweepyException as e:
            print(f"[POSTER] Failed to post tweet {i+1}: {e}")
            # If first tweet fails, abort whole thread
            if i == 0:
                return False
            # If follow-up fails, partial success is OK
            break

    return True


if __name__ == "__main__":
    # Quick test (will post a real tweet if keys are set)
    test_tweets = [
        "🧪 This is a test tweet from my bot. Ignore! #testing",
        "2/ This is the second tweet in the test thread.",
    ]
    result = post_tweet_thread(test_tweets)
    print(f"Post result: {result}")