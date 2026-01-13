import os
import time
import traceback
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import SendMail, dismiss_alert, bring_to_front


def _load_dotenv(env_path: Path):
    if not env_path.exists():
        return
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except Exception:
        traceback.print_exc()


class InstagramLogin:
    def __init__(self, driver=None, debug_port=None):
        print("Initializing InstagramLogin...")
        _load_dotenv(Path(__file__).resolve().parent / ".env")
        self.mailer = SendMail()
        self.debug_port = debug_port or int(os.getenv("INSTAGRAM_DEBUG_PORT", "5007"))
        self.driver = driver if driver else self.create_new_driver()

    def create_new_driver(self):
        print("Creating new WebDriver instance for Instagram...")
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.debug_port}")
        driver = webdriver.Chrome(options=options)
        return driver

    def is_already_logged_in(self):
        driver = self.driver
        markers = [
            (By.XPATH, "//svg[@aria-label='New post']"),
            (By.XPATH, "//span[normalize-space()='Create']"),
            (By.XPATH, "//a[contains(@href, '/accounts/edit')]"),
        ]
        for by, value in markers:
            if driver.find_elements(by, value):
                return True
        return False

    def is_login_form_visible(self):
        driver = self.driver
        return bool(driver.find_elements(By.NAME, "username")) and bool(
            driver.find_elements(By.NAME, "password")
        )

    def take_screenshot_and_send_email(self):
        screenshot_path = "/tmp/instagram-login.png"
        self.driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}.")
        self.mailer.send_email(
            "Instagram Login Required",
            "Login is required. Please see the attached screenshot.",
            screenshot_path,
            "instagram-login.png",
        )

    def try_password_login(self):
        username = os.getenv("IG_USERNAME") or os.getenv("INSTAGRAM_USERNAME")
        password = os.getenv("IG_PASSWORD") or os.getenv("INSTAGRAM_PASSWORD")
        if not username or not password:
            return False

        driver = self.driver
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, "username")))
            user_input = driver.find_element(By.NAME, "username")
            pass_input = driver.find_element(By.NAME, "password")
            user_input.clear()
            user_input.send_keys(username)
            pass_input.clear()
            pass_input.send_keys(password)
            pass_input.send_keys(Keys.ENTER)
            return True
        except Exception:
            traceback.print_exc()
            return False

    def check_and_act(self):
        driver = self.driver
        print("Navigating to Instagram...")
        driver.get("https://www.instagram.com/")
        time.sleep(2)
        dismiss_alert(driver)
        time.sleep(2)
        bring_to_front(["Instagram"])

        if self.is_already_logged_in():
            print("Instagram already logged in.")
            return

        try:
            WebDriverWait(driver, 15).until(
                lambda d: self.is_login_form_visible() or self.is_already_logged_in()
            )
        except Exception:
            print("Login form not detected yet.")

        if self.is_already_logged_in():
            print("Instagram logged in after page load.")
            return

        if self.try_password_login():
            print("Submitted username/password. Waiting for login to complete.")
            time.sleep(5)
            if self.is_already_logged_in():
                print("Instagram login succeeded.")
                return

        print("Instagram login requires manual action.")
        try:
            self.take_screenshot_and_send_email()
        except Exception:
            traceback.print_exc()

        start_time = time.time()
        while time.time() - start_time < 600:
            if self.is_already_logged_in():
                print("Instagram login completed.")
                return
            time.sleep(5)

        print("Instagram login timed out.")


if __name__ == "__main__":
    InstagramLogin().check_and_act()
