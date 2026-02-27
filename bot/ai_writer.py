# bot/ai_writer.py
import google.generativeai as genai
import os
import re
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")  # free tier model


TWEET_PROMPT = """
You are a tech news Twitter editor. Your job is to write an engaging tweet about a tech news article.

ARTICLE TITLE: {title}
ARTICLE SUMMARY: {summary}
SOURCE: {source}

INSTRUCTIONS:
1. First, classify the news as one of:
   - 🚨 BREAKING — confirmed official announcement
   - 🔥 JUST IN — very recent confirmed news
   - 👀 RUMOR — unconfirmed leak or speculation
   - 🛠️ LAUNCH — product/feature officially released
   - 📊 REPORT — data, survey, or analysis

2. Write ONE engaging tweet (max 250 characters including spaces)
   - Start with the emoji label from above
   - Be punchy and direct
   - Do NOT use more than 2 hashtags
   - Do NOT include the URL (we add it separately)
   - Do NOT use clickbait lies

3. Then write a SHORT THREAD (2-3 follow-up tweets) expanding on the story.
   Each follow-up tweet max 250 characters.
   Number them as 2/, 3/, 4/

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
LABEL: [emoji + category word]
TWEET1: [your main tweet text]
TWEET2: [thread continuation]
TWEET3: [thread continuation]
TWEET4: [optional final tweet with question to audience]
"""


def generate_tweet(article: dict) -> dict:
    """
    Use Gemini to generate a tweet + thread for an article.
    Returns dict with keys: label, tweets (list of strings)
    """
    prompt = TWEET_PROMPT.format(
        title=article["title"],
        summary=article.get("summary", "No summary available"),
        source=article.get("source", "Tech News"),
    )

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        print(f"[AI] Raw response:\n{raw}\n")
        return parse_ai_response(raw, article)

    except Exception as e:
        print(f"[AI] Gemini error: {e}")
        # Fallback: plain tweet without AI
        return {
            "label": "🔥 JUST IN",
            "tweets": [
                f"🔥 JUST IN: {article['title'][:200]} #{article['source'].replace(' ','')}"
            ]
        }


def parse_ai_response(raw: str, article: dict) -> dict:
    """Parse the structured Gemini response into usable parts."""
    lines = raw.strip().split("\n")
    result = {"label": "🔥 JUST IN", "tweets": []}

    for line in lines:
        line = line.strip()
        if line.startswith("LABEL:"):
            result["label"] = line.replace("LABEL:", "").strip()
        elif line.startswith("TWEET1:"):
            tweet = line.replace("TWEET1:", "").strip()
            # Add article URL and source to first tweet
            tweet = f"{tweet}\n\n{article['link']}"
            result["tweets"].append(tweet)
        elif line.startswith("TWEET2:"):
            result["tweets"].append(line.replace("TWEET2:", "").strip())
        elif line.startswith("TWEET3:"):
            result["tweets"].append(line.replace("TWEET3:", "").strip())
        elif line.startswith("TWEET4:"):
            result["tweets"].append(line.replace("TWEET4:", "").strip())

    # Safety fallback if parsing failed
    if not result["tweets"]:
        result["tweets"] = [f"🔥 {article['title'][:220]}\n\n{article['link']}"]

    return result


if __name__ == "__main__":
    # Quick test
    test_article = {
        "title": "Apple announces M4 MacBook Air with 24-hour battery life",
        "summary": "Apple today announced the new MacBook Air featuring the M4 chip...",
        "source": "TechCrunch",
        "link": "https://techcrunch.com/example",
    }
    result = generate_tweet(test_article)
    print("\n=== GENERATED TWEETS ===")
    for i, t in enumerate(result["tweets"], 1):
        print(f"\n[{i}] {t}")