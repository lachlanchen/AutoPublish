import os
import time
import traceback

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils import SendMail, bring_to_front, dismiss_alert, log_html_snapshot, safe_get


BILIBILI_UPLOAD_URL = "https://member.bilibili.com/platform/upload/video/frame"


class BilibiliLogin:
    def __init__(self, driver=None, port="5005"):
        print("Initializing BilibiliLogin class...")
        self.mailer = SendMail()
        self.port = port
        self.driver = driver if driver else self.create_new_driver()

    def create_new_driver(self):
        print("Creating new WebDriver instance...")
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.port}")
        return webdriver.Chrome(options=options)

    def _login_wait_seconds(self):
        try:
            return max(60, int(os.environ.get("AUTOPUBLISH_LOGIN_WAIT_SECONDS", "1800")))
        except Exception:
            return 1800

    def _expected_account_names(self):
        env_names = os.environ.get("BILIBILI_ACCOUNT_NAMES") or os.environ.get("BILIBILI_ACCOUNT_NAME")
        if env_names:
            return [name.strip() for name in env_names.split(",") if name.strip()]
        return [
            "LazyingArt懒人艺术",
            "LazyingArt懶人藝術",
            "LazyingArt",
            "懒人艺术",
            "懶人藝術",
            "陈苗",
        ]

    def _visible_elements(self, by, selector):
        try:
            elements = self.driver.find_elements(by, selector)
        except Exception:
            return []
        visible = []
        for element in elements:
            try:
                if element.is_displayed():
                    visible.append(element)
            except Exception:
                continue
        return visible

    def is_already_logged_in(self):
        ready_selectors = [
            (By.CSS_SELECTOR, 'input[type="file"][accept*="mp4"]'),
            (By.CSS_SELECTOR, 'input[type="file"][accept*="video"]'),
            (By.XPATH, '//*[contains(text(),"上传视频")]'),
            (By.XPATH, '//*[contains(text(),"立即投稿")]'),
            (By.XPATH, '//*[contains(text(),"稿件标题")]'),
        ]
        for by, selector in ready_selectors:
            if self._visible_elements(by, selector):
                print(f"Bilibili upload UI detected with selector: {selector}")
                return True

        for name in self._expected_account_names():
            xpath = f"//*[contains(normalize-space(.), '{name}')]"
            try:
                if self.driver.find_elements(By.XPATH, xpath):
                    print(f"Bilibili account marker detected: {name}")
                    return True
            except Exception:
                continue
        return False

    def click_login_button(self):
        selectors = [
            (By.XPATH, '//button[contains(normalize-space(.),"登录")]'),
            (By.XPATH, '//*[contains(@class,"login") and contains(normalize-space(.),"登录")]'),
            (By.XPATH, '//*[contains(normalize-space(.),"登录") and (self::span or self::div or self::a)]'),
        ]
        for by, selector in selectors:
            try:
                element = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((by, selector)))
                element.click()
                print(f"Clicked Bilibili login element using selector: {selector}")
                return True
            except Exception:
                continue
        return False

    def click_qr_tab(self):
        selectors = [
            (By.XPATH, '//*[contains(text(),"扫码登录")]'),
            (By.XPATH, '//*[contains(text(),"二维码登录")]'),
            (By.XPATH, '//*[contains(text(),"扫码")]'),
        ]
        for by, selector in selectors:
            try:
                elements = self.driver.find_elements(by, selector)
            except Exception:
                continue
            for element in elements:
                try:
                    if element.is_displayed():
                        element.click()
                        print(f"Selected Bilibili QR tab with selector: {selector}")
                        return True
                except Exception:
                    continue
        return False

    def is_login_ui_visible(self):
        markers = [
            (By.XPATH, '//*[contains(text(),"扫码登录")]'),
            (By.XPATH, '//*[contains(text(),"二维码登录")]'),
            (By.XPATH, '//*[contains(text(),"登录")]'),
            (By.CSS_SELECTOR, 'img[src^="data:image"]'),
            (By.CSS_SELECTOR, "canvas"),
        ]
        return any(self._visible_elements(by, selector) for by, selector in markers)

    def wait_for_login_visual(self, timeout=20):
        def _has_login_visual(_driver):
            if self._visible_elements(By.CSS_SELECTOR, 'img[src^="data:image"]'):
                return True
            if self._visible_elements(By.CSS_SELECTOR, "canvas"):
                return True
            return self.is_login_ui_visible()

        try:
            WebDriverWait(self.driver, timeout).until(_has_login_visual)
            return True
        except Exception:
            return False

    def is_qr_outdated(self):
        texts = [
            "二维码已失效",
            "二维码已过期",
            "请刷新",
            "刷新二维码",
        ]
        for text in texts:
            if self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]"):
                return True
        return False

    def refresh_qr_code(self):
        selectors = [
            (By.XPATH, '//*[contains(text(),"刷新")]'),
            (By.XPATH, '//*[contains(text(),"点击刷新")]'),
        ]
        for by, selector in selectors:
            for element in self._visible_elements(by, selector):
                try:
                    element.click()
                    print("Clicked Bilibili QR refresh control.")
                    return True
                except Exception:
                    continue

        print("Refreshing Bilibili upload page as QR refresh fallback.")
        self.driver.refresh()
        time.sleep(3)
        self.click_login_button()
        self.click_qr_tab()
        return False

    def take_screenshot_and_send_email(self, subject=None, content=None):
        screenshot_path = "/tmp/bilibili-login.png"
        self.driver.save_screenshot(screenshot_path)
        print(f"Bilibili login screenshot saved to {screenshot_path}.")
        self.mailer.send_email(
            subject or "Bilibili Login Required",
            content or "Login is required. Please see the attached screenshot including the QR code.",
            screenshot_path,
            "bilibili-login.png",
        )

    def check_and_act(self):
        print("Navigating to the Bilibili upload page...")
        bring_to_front(["哔哩哔哩", "bilibili", "Bilibili"])
        safe_get(self.driver, BILIBILI_UPLOAD_URL, timeout=45, label="Bilibili upload page")
        time.sleep(1)
        dismiss_alert(self.driver)
        time.sleep(3)
        bring_to_front(["哔哩哔哩", "bilibili", "Bilibili"])

        if self.is_already_logged_in():
            print("Already logged in to Bilibili.")
            return True

        try:
            self.click_login_button()
            self.click_qr_tab()
            time.sleep(3)
            if not self.wait_for_login_visual(timeout=20):
                log_html_snapshot(self.driver, "bilibili", "login_visual_missing")
                self.take_screenshot_and_send_email(
                    subject="Bilibili Login Page Changed",
                    content="Bilibili login is required, but the expected QR/login visual was not detected. Please inspect the screenshot.",
                )
                raise RuntimeError("Bilibili login visual was not detected.")
            self.take_screenshot_and_send_email()
        except Exception:
            if self.is_already_logged_in():
                print("Bilibili became logged in while opening the login UI.")
                return True
            print("Bilibili login UI was not usable.")
            traceback.print_exc()
            raise

        wait_seconds = self._login_wait_seconds()
        start_time = time.time()
        last_email_time = start_time
        while time.time() - start_time < wait_seconds:
            if self.is_already_logged_in():
                print("Bilibili logged in successfully.")
                return True

            if self.is_qr_outdated():
                self.refresh_qr_code()
                time.sleep(5)
                self.take_screenshot_and_send_email()
                last_email_time = time.time()

            if time.time() - last_email_time > 300 and self.is_login_ui_visible():
                self.take_screenshot_and_send_email(
                    subject="Bilibili Login Still Required",
                    content="Bilibili is still waiting for QR login. Please scan the attached QR screenshot.",
                )
                last_email_time = time.time()

            time.sleep(5)

        raise RuntimeError(f"Bilibili login was not completed within {wait_seconds} seconds.")


if __name__ == "__main__":
    BilibiliLogin().check_and_act()
