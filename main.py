# main.py
import os
import json
import sys
from dotenv import load_dotenv

from bot.fetcher import fetch_latest_articles, load_posted_ids, save_posted_ids
from bot.image_extractor import get_article_image
from bot.ai_writer import generate_tweet
from bot.poster import post_tweet_thread

load_dotenv()

ARTICLES_PER_RUN = 1  # post 1 article per daily run (safe, avoids spam flags)


def main():
    print("=" * 50)
    print("  TECH NEWS BOT — STARTING RUN")
    print("=" * 50)

    # ── 1. Fetch new articles ──────────────────────────
    print("\n[1/5] Fetching latest tech news...")
    articles = fetch_latest_articles(max_articles=10)

    if not articles:
        print("[MAIN] No new articles found. Exiting.")
        sys.exit(0)

    # ── 2. Pick the best article ───────────────────────
    # For now: just take the first one
    # You can add scoring logic here later (by source priority, keyword match etc.)
    article = articles[0]
    print(f"\n[2/5] Selected article:\n  → {article['title']}")

    # ── 3. Get article image ───────────────────────────
    print("\n[3/5] Extracting article image...")
    image_path = get_article_image(article["link"])
    if image_path:
        print(f"  → Image ready: {image_path}")
    else:
        print("  → No image found, will post text-only")

    # ── 4. Generate tweet with AI ──────────────────────
    print("\n[4/5] Generating tweet with Gemini AI...")
    tweet_data = generate_tweet(article)
    print(f"  → Label: {tweet_data['label']}")
    print(f"  → Tweets to post: {len(tweet_data['tweets'])}")
    for i, t in enumerate(tweet_data["tweets"], 1):
        print(f"\n  [{i}] {t[:100]}...")

    # ── 5. Post to X ──────────────────────────────────
    print("\n[5/5] Posting to X...")
    success = post_tweet_thread(tweet_data["tweets"], image_path=image_path)

    if success:
        print("\n✅ Successfully posted!")
        # Mark article as posted
        posted_ids = load_posted_ids()
        posted_ids.append(article["id"])
        save_posted_ids(posted_ids)
        print(f"  → Saved article ID to dedup log")
    else:
        print("\n❌ Posting failed.")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("  BOT RUN COMPLETE")
    print("=" * 50)


if __name__ == "__main__":
    main()