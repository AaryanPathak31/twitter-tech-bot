# bot/image_extractor.py
import requests
from bs4 import BeautifulSoup
import os
import hashlib

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
IMAGE_DIR = "/tmp/bot_images"
MAX_IMAGE_SIZE_MB = 5  # X limit is 5MB for images


def ensure_image_dir():
    os.makedirs(IMAGE_DIR, exist_ok=True)


def extract_og_image(article_url: str) -> str | None:
    """
    Scrape the og:image or twitter:image meta tag from an article URL.
    Returns the image URL string, or None if not found.
    """
    try:
        resp = requests.get(article_url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"[IMAGE] Failed to fetch article page: {e}")
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    # Try og:image first
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        return og["content"]

    # Fallback: twitter:image
    tw = soup.find("meta", attrs={"name": "twitter:image"})
    if tw and tw.get("content"):
        return tw["content"]

    # Fallback: first <img> in article body
    img = soup.find("img", src=True)
    if img:
        src = img["src"]
        if src.startswith("http"):
            return src

    print(f"[IMAGE] No og:image found for {article_url}")
    return None


def download_image(image_url: str) -> str | None:
    """
    Download image to /tmp/. Returns local file path or None.
    """
    ensure_image_dir()

    # Generate filename from URL hash
    url_hash = hashlib.md5(image_url.encode()).hexdigest()[:10]
    ext = image_url.split("?")[0].split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png", "gif", "webp"]:
        ext = "jpg"
    filepath = os.path.join(IMAGE_DIR, f"{url_hash}.{ext}")

    # Skip download if already cached
    if os.path.exists(filepath):
        return filepath

    try:
        resp = requests.get(image_url, headers=HEADERS, timeout=15, stream=True)
        resp.raise_for_status()

        # Check size before downloading
        content_length = resp.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
            print(f"[IMAGE] Image too large, skipping")
            return None

        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)

        print(f"[IMAGE] Downloaded to {filepath}")
        return filepath

    except Exception as e:
        print(f"[IMAGE] Download failed: {e}")
        return None


def get_article_image(article_url: str) -> str | None:
    """
    Full pipeline: extract OG image URL then download it.
    Returns local file path or None.
    """
    image_url = extract_og_image(article_url)
    if not image_url:
        return None
    return download_image(image_url)


if __name__ == "__main__":
    # Quick test
    test_url = "https://techcrunch.com"
    path = get_article_image(test_url)
    print(f"Image saved to: {path}")