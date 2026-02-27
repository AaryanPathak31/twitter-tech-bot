# bot/ai_writer.py
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])

TWEET_PROMPT = """
You are a tech news Twitter editor. Write an engaging tweet about this article.

ARTICLE TITLE: {title}
ARTICLE SUMMARY: {summary}
SOURCE: {source}

INSTRUCTIONS:
1. Classify as one of:
   - 🚨 BREAKING — confirmed official announcement
   - 🔥 JUST IN — very recent confirmed news
   - 👀 RUMOR — unconfirmed leak or speculation
   - 🛠️ LAUNCH — product/feature officially released
   - 📊 REPORT — data, survey, or analysis

2. Write ONE tweet (max 250 characters)
   - Start with the emoji label
   - Be punchy and direct
   - Max 2 hashtags
   - Do NOT include the URL

3. Write 2-3 follow-up thread tweets (max 250 chars each)
   Numbered as 2/, 3/, 4/

FORMAT EXACTLY LIKE THIS:
LABEL: [emoji + category]
TWEET1: [main tweet]
TWEET2: [thread continuation]
TWEET3: [thread continuation]
TWEET4: [optional question to audience]
"""

def generate_tweet(article: dict) -> dict:
    prompt = TWEET_PROMPT.format(
        title=article["title"],
        summary=article.get("summary", "No summary available"),
        source=article.get("source", "Tech News"),
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7,
        )
        raw = response.choices[0].message.content.strip()
        print(f"[AI] Raw response:\n{raw}\n")
        return parse_ai_response(raw, article)

    except Exception as e:
        print(f"[AI] Groq error: {e}")
        return {
            "label": "🔥 JUST IN",
            "tweets": [
                f"🔥 JUST IN: {article['title'][:200]}\n\n{article['link']}"
            ]
        }


def parse_ai_response(raw: str, article: dict) -> dict:
    result = {"label": "🔥 JUST IN", "tweets": []}

    for line in raw.strip().split("\n"):
        line = line.strip()
        if line.startswith("LABEL:"):
            result["label"] = line.replace("LABEL:", "").strip()
        elif line.startswith("TWEET1:"):
            tweet = line.replace("TWEET1:", "").strip()
            tweet = f"{tweet}\n\n{article['link']}"
            result["tweets"].append(tweet)
        elif line.startswith("TWEET2:"):
            result["tweets"].append(line.replace("TWEET2:", "").strip())
        elif line.startswith("TWEET3:"):
            result["tweets"].append(line.replace("TWEET3:", "").strip())
        elif line.startswith("TWEET4:"):
            result["tweets"].append(line.replace("TWEET4:", "").strip())

    if not result["tweets"]:
        result["tweets"] = [
            f"🔥 {article['title'][:220]}\n\n{article['link']}"
        ]
    return result
