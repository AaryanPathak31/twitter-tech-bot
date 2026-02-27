# bot/poster.py
import os
import time
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
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
    options.add_argument("--disable-extensions")
    options.add_argument("--dns-prefetch-disable")
    options.add_argument("--disable-web-security")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    chromedriver = shutil.which("chromedriver") or "/usr/bin/chromedriver"
    print(f"[SELENIUM] Using: {chromedriver}")
    driver = webdriver.Chrome(service=Service(chromedriver), options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        """
    })
    return driver


def js_click(driver, element):
    """Click element using JavaScript — avoids interception errors."""
    driver.execute_script("arguments[0].click();", element)


def js_type(driver, element, text):
    """Type text using JavaScript — avoids stale element issues."""
    driver.execute_script("arguments[0].focus();", element)
    for char in text:
        element.send_keys(char)
        time.sleep(0.05)


def wait_and_find(driver, css, timeout=30):
    """Wait for element and return it fresh."""
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css))
    )
    time.sleep(1.5)
    return driver.find_element(By.CSS_SELECTOR, css)


def login_to_x(driver):
    username = os.environ["X_USERNAME"]
    password = os.environ["X_PASSWORD"]

    print("[SELENIUM] Loading X login...")
    driver.get("https://x.com/i/flow/login")
    time.sleep(8)

    # Screenshot to see what page loaded
    driver.save_screenshot("/tmp/s0_loginpage.png")
    print(f"[SELENIUM] Page title: {driver.title}")
    print(f"[SELENIUM] Current URL: {driver.current_url}")

    # ── Username ──────────────────────────────────────────
    print("[SELENIUM] Typing username...")
    try:
        el = wait_and_find(driver, 'input[autocomplete="username"]')
        js_type(driver, el, username)
        time.sleep(2)
        driver.save_screenshot("/tmp/s1_after_username.png")

        # Find and click Next button
        all_buttons = driver.find_elements(By.XPATH, '//button | //div[@role="button"]')
        print(f"[SELENIUM] Found {len(all_buttons)} buttons")
        clicked = False
        for btn in all_buttons:
            try:
                txt = btn.text.strip().lower()
                if txt in ["next", "log in", "signin"]:
                    js_click(driver, btn)
                    clicked = True
                    print(f"[SELENIUM] Clicked button: {btn.text}")
                    break
            except Exception:
                continue
        if not clicked:
            print("[SELENIUM] No Next button found, pressing Enter")
            el.send_keys("\n")
    except Exception as e:
        driver.save_screenshot("/tmp/s1_fail.png")
        raise Exception(f"Username step failed: {e}")

    time.sleep(5)
    driver.save_screenshot("/tmp/s2_after_next.png")
    print(f"[SELENIUM] URL after Next: {driver.current_url}")

    # ── Extra verification step ───────────────────────────
    try:
        extra = driver.find_element(
            By.CSS_SELECTOR, 'input[data-testid="ocfEnterTextTextInput"]'
        )
        print("[SELENIUM] Extra verification detected, entering username...")
        js_type(driver, extra, username)
        extra.send_keys("\n")
        time.sleep(4)
    except Exception:
        print("[SELENIUM] No extra verification needed")

    # ── Password — try multiple selectors ─────────────────
    print("[SELENIUM] Looking for password field...")
    driver.save_screenshot("/tmp/s3_before_password.png")

    password_selectors = [
        'input[name="password"]',
        'input[type="password"]',
        'input[autocomplete="current-password"]',
        'input[data-testid="password"]',
    ]

    pw_el = None
    for sel in password_selectors:
        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, sel))
            )
            time.sleep(2)
            pw_el = driver.find_element(By.CSS_SELECTOR, sel)
            print(f"[SELENIUM] Found password field: {sel}")
            break
        except Exception:
            print(f"[SELENIUM] Selector failed: {sel}")
            continue

    if not pw_el:
        # Last resort: find any password input on page
        try:
            pw_el = driver.find_element(By.XPATH, '//input[@type="password"]')
            print("[SELENIUM] Found password via XPATH")
        except Exception:
            driver.save_screenshot("/tmp/s3_no_password.png")
            # Print page source snippet for debugging
            print("[SELENIUM] Page source snippet:")
            print(driver.page_source[:2000])
            raise Exception("Cannot find password field")

    js_type(driver, pw_el, password)
    time.sleep(2)
    driver.save_screenshot("/tmp/s4_after_password_typed.png")

    # Click login button
    all_buttons = driver.find_elements(By.XPATH, '//button | //div[@role="button"]')
    clicked = False
    for btn in all_buttons:
        try:
            txt = btn.text.strip().lower()
            if txt in ["log in", "login", "sign in", "signin"]:
                js_click(driver, btn)
                clicked = True
                print(f"[SELENIUM] Clicked: {btn.text}")
                break
        except Exception:
            continue
    if not clicked:
        pw_el.send_keys("\n")
        print("[SELENIUM] Pressed Enter on password")

    time.sleep(8)
    driver.save_screenshot("/tmp/s5_after_login.png")
    print(f"[SELENIUM] Final URL: {driver.current_url}")

    if "login" in driver.current_url or "flow" in driver.current_url:
        print("[SELENIUM] Page source snippet:")
        print(driver.page_source[:3000])
        raise Exception(f"Login failed. URL: {driver.current_url}")

    print("[SELENIUM] ✅ Login successful!")

def post_single_tweet(driver, text, image_path=None):
    """Post one tweet via compose page."""
    print("[SELENIUM] Opening compose page...")
    driver.get("https://x.com/compose/tweet")
    time.sleep(6)

    # ── Find tweet box using multiple strategies ──────────
    tweet_box = None
    selectors = [
        '[data-testid="tweetTextarea_0"]',
        '.public-DraftEditor-content',
        '[contenteditable="true"]',
        'div[role="textbox"]',
    ]

    for sel in selectors:
        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, sel))
            )
            time.sleep(2)
            tweet_box = driver.find_element(By.CSS_SELECTOR, sel)
            print(f"[SELENIUM] Found tweet box with: {sel}")
            break
        except Exception:
            continue

    if not tweet_box:
        driver.save_screenshot("/tmp/s4_no_tweetbox.png")
        raise Exception("Could not find tweet box")

    # ── Type tweet using JavaScript ───────────────────────
    js_click(driver, tweet_box)
    time.sleep(1)
    # Use JS to set text content directly
    driver.execute_script(
        "arguments[0].innerText = arguments[1];",
        tweet_box, text
    )
    time.sleep(1)
    # Trigger input event so X registers the text
    driver.execute_script("""
        arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
        arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
    """, tweet_box)
    time.sleep(2)

    # ── Attach image if available ─────────────────────────
    if image_path and os.path.exists(image_path):
        try:
            file_input = driver.find_element(
                By.CSS_SELECTOR, 'input[accept*="image"]'
            )
            file_input.send_keys(os.path.abspath(image_path))
            time.sleep(5)
            print("[SELENIUM] Image attached!")
        except Exception as e:
            print(f"[SELENIUM] Image skipped: {e}")

    # ── Click Post button ─────────────────────────────────
    post_selectors = [
        '[data-testid="tweetButtonInline"]',
        '[data-testid="tweetButton"]',
    ]
    posted = False
    for sel in post_selectors:
        try:
            btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
            )
            time.sleep(1)
            btn = driver.find_element(By.CSS_SELECTOR, sel)
            js_click(driver, btn)
            time.sleep(5)
            print("[SELENIUM] ✅ Tweet posted!")
            posted = True
            break
        except Exception:
            continue

    if not posted:
        driver.save_screenshot("/tmp/s5_no_postbtn.png")
        raise Exception("Could not find Post button")


def post_tweet_thread(tweets: list, image_path: str = None) -> bool:
    driver = get_driver()
    try:
        login_to_x(driver)

        for i, tweet_text in enumerate(tweets):
            print(f"\n[SELENIUM] Posting tweet {i+1}/{len(tweets)}...")
            img = image_path if i == 0 else None
            post_single_tweet(driver, tweet_text[:280], img)
            if i < len(tweets) - 1:
                time.sleep(5)

        return True

    except Exception as e:
        print(f"[SELENIUM] Fatal: {e}")
        try:
            driver.save_screenshot("/tmp/fatal_error.png")
        except Exception:
            pass
        return False
    finally:
        driver.quit()
