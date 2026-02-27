# bot/poster.py
import os
import time
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()


def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--remote-debugging-port=9222")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    chromedriver_path = shutil.which("chromedriver") or "/usr/bin/chromedriver"
    print(f"[SELENIUM] ChromeDriver: {chromedriver_path}")
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


def safe_find_and_type(driver, css, text, timeout=30):
    """Wait for element, re-find it fresh, then type. Avoids stale element."""
    wait = WebDriverWait(driver, timeout)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))
    time.sleep(2)  # let page fully settle
    # Re-find fresh every time to avoid stale reference
    el = driver.find_element(By.CSS_SELECTOR, css)
    el.click()
    time.sleep(1)
    el.send_keys(text)
    time.sleep(1)
    el.send_keys(Keys.ENTER)
    time.sleep(3)


def login_to_x(driver):
    username = os.environ["X_USERNAME"]
    password = os.environ["X_PASSWORD"]

    print("[SELENIUM] Going to X login page...")
    driver.get("https://x.com/i/flow/login")
    time.sleep(6)  # full page load

    wait = WebDriverWait(driver, 30)

    # ── Step 1: Username ─────────────────────────────────
    print("[SELENIUM] Entering username...")
    wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, 'input[autocomplete="username"]')
    ))
    time.sleep(2)
    user_input = driver.find_element(By.CSS_SELECTOR, 'input[autocomplete="username"]')
    user_input.click()
    time.sleep(1)
    # Type character by character to avoid detection
    for char in username:
        user_input.send_keys(char)
        time.sleep(0.05)
    time.sleep(1)
    user_input.send_keys(Keys.ENTER)
    time.sleep(4)

    # ── Step 2: Possible extra verification ──────────────
    try:
        extra = driver.find_element(
            By.CSS_SELECTOR, 'input[data-testid="ocfEnterTextTextInput"]'
        )
        print("[SELENIUM] Extra verification step detected...")
        extra.click()
        extra.send_keys(username)
        extra.send_keys(Keys.ENTER)
        time.sleep(3)
    except Exception:
        pass

    # ── Step 3: Password ─────────────────────────────────
    print("[SELENIUM] Entering password...")
    wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, 'input[name="password"]')
    ))
    time.sleep(2)
    pass_input = driver.find_element(By.CSS_SELECTOR, 'input[name="password"]')
    pass_input.click()
    time.sleep(1)
    for char in password:
        pass_input.send_keys(char)
        time.sleep(0.05)
    time.sleep(1)
    pass_input.send_keys(Keys.ENTER)
    time.sleep(7)

    # ── Verify login succeeded ───────────────────────────
    current_url = driver.current_url
    print(f"[SELENIUM] After login URL: {current_url}")
    if "login" in current_url or "error" in current_url:
        driver.save_screenshot("/tmp/login_failed.png")
        raise Exception(f"Login may have failed. URL: {current_url}")
    print("[SELENIUM] Login successful!")


def compose_tweet(driver, tweet_text, image_path=None):
    """Navigate to compose page and post a single tweet."""
    wait = WebDriverWait(driver, 30)

    driver.get("https://x.com/compose/tweet")
    time.sleep(6)

    # Find tweet box fresh
    print("[SELENIUM] Finding tweet box...")
    wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, '[data-testid="tweetTextarea_0"]')
    ))
    time.sleep(2)
    tweet_box = driver.find_element(By.CSS_SELECTOR, '[data-testid="tweetTextarea_0"]')
    tweet_box.click()
    time.sleep(1)

    # Type tweet character by character
    for char in tweet_text:
        tweet_box.send_keys(char)
        time.sleep(0.03)
    time.sleep(2)

    # Attach image if provided
    if image_path and os.path.exists(image_path):
        try:
            file_input = driver.find_element(By.CSS_SELECTOR, 'input[accept*="image"]')
            file_input.send_keys(os.path.abspath(image_path))
            time.sleep(5)
            print("[SELENIUM] Image attached")
        except Exception as e:
            print(f"[SELENIUM] Image attach skipped: {e}")

    # Re-find post button fresh and click
    print("[SELENIUM] Clicking post button...")
    time.sleep(2)
    post_btn = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, '[data-testid="tweetButtonInline"]')
    ))
    # Re-find fresh right before clicking
    post_btn = driver.find_element(By.CSS_SELECTOR, '[data-testid="tweetButtonInline"]')
    post_btn.click()
    time.sleep(5)


def post_tweet_thread(tweets: list, image_path: str = None) -> bool:
    driver = get_driver()

    try:
        login_to_x(driver)

        for i, tweet_text in enumerate(tweets):
            print(f"[SELENIUM] Posting tweet {i+1}/{len(tweets)}...")
            img = image_path if i == 0 else None
            compose_tweet(driver, tweet_text, img)
            print(f"[SELENIUM] ✅ Tweet {i+1} posted!")
            if i < len(tweets) - 1:
                time.sleep(5)

        return True

    except Exception as e:
        print(f"[SELENIUM] Fatal error: {e}")
        try:
            driver.save_screenshot("/tmp/selenium_error.png")
            print("[SELENIUM] Screenshot saved to /tmp/selenium_error.png")
        except Exception:
            pass
        return False

    finally:
        driver.quit()
