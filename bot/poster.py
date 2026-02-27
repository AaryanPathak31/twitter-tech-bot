# bot/poster.py
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
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
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


def login_to_x(driver):
    username = os.environ["X_USERNAME"]
    password = os.environ["X_PASSWORD"]

    print("[SELENIUM] Navigating to X login...")
    driver.get("https://x.com/i/flow/login")
    time.sleep(5)

    wait = WebDriverWait(driver, 20)

    # Enter username
    user_input = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, 'input[autocomplete="username"]')
    ))
    user_input.click()
    user_input.send_keys(username)
    user_input.send_keys(Keys.ENTER)
    time.sleep(3)

    # Handle possible "Enter phone/email" extra step
    try:
        extra = driver.find_element(By.CSS_SELECTOR, 'input[data-testid="ocfEnterTextTextInput"]')
        extra.send_keys(username)
        extra.send_keys(Keys.ENTER)
        time.sleep(3)
    except:
        pass

    # Enter password
    pass_input = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, 'input[name="password"]')
    ))
    pass_input.click()
    pass_input.send_keys(password)
    pass_input.send_keys(Keys.ENTER)
    time.sleep(6)
    print("[SELENIUM] Login complete")


def post_tweet_thread(tweets: list, image_path: str = None) -> bool:
    driver = get_driver()

    try:
        login_to_x(driver)

        for i, tweet_text in enumerate(tweets):
            print(f"[SELENIUM] Posting tweet {i+1}...")
            driver.get("https://x.com/compose/tweet")
            time.sleep(5)

            wait = WebDriverWait(driver, 20)

            tweet_box = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[data-testid="tweetTextarea_0"]')
            ))
            tweet_box.click()
            time.sleep(1)
            tweet_box.send_keys(tweet_text)
            time.sleep(2)

            # Attach image to first tweet only
            if i == 0 and image_path and os.path.exists(image_path):
                try:
                    file_input = driver.find_element(
                        By.CSS_SELECTOR, 'input[accept*="image"]'
                    )
                    file_input.send_keys(os.path.abspath(image_path))
                    time.sleep(5)
                    print("[SELENIUM] Image attached")
                except Exception as e:
                    print(f"[SELENIUM] Image attach skipped: {e}")

            # Click Post button
            post_btn = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '[data-testid="tweetButtonInline"]')
            ))
            post_btn.click()
            time.sleep(5)
            print(f"[SELENIUM] Tweet {i+1} posted!")

            if i < len(tweets) - 1:
                time.sleep(5)

        return True

    except Exception as e:
        print(f"[SELENIUM] Error: {e}")
        try:
            driver.save_screenshot("/tmp/selenium_error.png")
            print("[SELENIUM] Screenshot saved to /tmp/selenium_error.png")
        except:
            pass
        return False

    finally:
        driver.quit()
