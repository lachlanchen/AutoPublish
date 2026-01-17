from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pathlib import Path
import os
import time
import traceback

from utils import SendMail
from utils import dismiss_alert, bring_to_front, log_html_snapshot


class DouyinLogin:
    def __init__(self, driver=None):
        print("Initializing DouyinLogin class...")
        self._load_dotenv(Path(__file__).resolve().parent / ".env")
        self.mailer = SendMail(
            sendgrid_api_key=None,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
        )
        self.driver = driver if driver else self.create_new_driver()

    def _load_dotenv(self, env_path: Path):
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

    def _get_second_verify_password(self):
        password = os.getenv("DOUYIN_LOGIN_PASSWORD") or os.getenv("DOUYIN_PASSWORD")
        if password is None:
            return None
        password = password.strip()
        return password or None

    def create_new_driver(self):
        print("Creating new WebDriver instance...")
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:5004")
        driver = webdriver.Chrome(options=options)
        return driver

    def click_login_button(self):
        selectors = [
            (By.CSS_SELECTOR, "span.login"),
            (By.XPATH, "//button[.//span[contains(text(), '登录')] or contains(text(), '登录')]"),
            (By.XPATH, "//span[contains(text(), '登录')]"),
        ]
        for by, selector in selectors:
            try:
                login_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((by, selector))
                )
                login_button.click()
                print(f"Clicked login element using selector: {selector}")
                return True
            except Exception:
                continue
        return False

    def click_qr_tab(self):
        try:
            tab = self.driver.find_element(By.XPATH, "//*[contains(text(), '扫码登录')]")
            if tab.is_displayed():
                tab.click()
                print("Ensured QR login tab is selected.")
                return True
        except Exception:
            return False
        return False

    def _find_qr_images(self):
        images = self.driver.find_elements(By.CSS_SELECTOR, "img[src^='data:image/png;base64']")
        qr_images = []
        for image in images:
            size = image.size or {}
            if size.get("width", 0) >= 100 and size.get("height", 0) >= 100:
                qr_images.append(image)
        return qr_images

    def wait_for_qr_code(self, timeout=20):
        try:
            WebDriverWait(self.driver, timeout).until(lambda d: self._find_qr_images())
            return True
        except TimeoutException:
            return False

    def is_login_ui_visible(self):
        if self._find_qr_images():
            return True
        markers = [
            (By.XPATH, "//*[contains(text(), '扫码登录')]"),
            (By.XPATH, "//*[contains(text(), '抖音创作者中心')]"),
            (By.CSS_SELECTOR, "span.login"),
        ]
        for by, selector in markers:
            if self.driver.find_elements(by, selector):
                return True
        return False

    def report_layout_change(self):
        print("Douyin login UI not detected. Page structure may have changed.")
        log_html_snapshot(self.driver, "douyin", "layout_change")
        self.take_screenshot_and_send_email(
            subject="Douyin Login Page Changed",
            content="Could not detect the expected Douyin login UI. Please check the page layout.",
        )

    def is_second_verify_visible(self):
        markers = [
            (By.CSS_SELECTOR, "#uc-second-verify"),
            (By.XPATH, "//*[contains(text(), '身份验证')]"),
            (By.XPATH, "//*[contains(text(), '验证登录密码')]"),
        ]
        for by, selector in markers:
            if self.driver.find_elements(by, selector):
                return True
        return False

    def click_password_verify_option(self):
        try:
            options = self.driver.find_elements(By.XPATH, "//*[contains(text(), '验证登录密码')]")
            for option in options:
                if not option.is_displayed():
                    continue
                try:
                    container = option.find_element(
                        By.XPATH,
                        "./ancestor::*[contains(@class, 'uc_verification_component_list_item')][1]",
                    )
                except Exception:
                    container = option
                container.click()
                return True
        except Exception:
            return False
        return False

    def fill_password_and_submit(self, password: str):
        try:
            input_el = WebDriverWait(self.driver, 6).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//input[@type='password' and contains(@placeholder, '密码')]")
                )
            )
            input_el.clear()
            input_el.send_keys(password)
        except Exception:
            return False

        selectors = [
            (By.XPATH, "//div[contains(@class, 'primary') and contains(text(), '验证')]"),
            (By.XPATH, "//button[contains(text(), '验证')]"),
        ]
        for by, selector in selectors:
            try:
                button = WebDriverWait(self.driver, 6).until(
                    EC.element_to_be_clickable((by, selector))
                )
                button.click()
                return True
            except Exception:
                continue
        return False

    def handle_second_verify(self):
        if not self.is_second_verify_visible():
            return False

        password = self._get_second_verify_password()
        if not password:
            print("Second verification needs password. Set DOUYIN_LOGIN_PASSWORD in .env.")
            self.take_screenshot_and_send_email(
                subject="Douyin Second Verify Needed",
                content="Second verification requires password. Set DOUYIN_LOGIN_PASSWORD in .env.",
            )
            return False

        self.click_password_verify_option()
        time.sleep(1)
        if self.fill_password_and_submit(password):
            print("Submitted second verification password.")
            return True
        return False

    def check_and_act(self):
        print("Navigating to the Douyin URL...")
        url = 'https://creator.douyin.com/creator-micro/home'
        self.driver.get(url)

        time.sleep(1)

        dismiss_alert(self.driver)

        time.sleep(3)

        bring_to_front(["抖音"])

        print("Checking login status...")
        if self.is_already_logged_in():
            print("Already logged in.")
            return

        try:
            self.click_login_button()
            self.click_qr_tab()
            time.sleep(5)  # Allow some time for the QR code to load

            if not self.wait_for_qr_code():
                if not self.is_login_ui_visible():
                    self.report_layout_change()
                else:
                    print("QR code not detected yet.")
                return

            self.take_screenshot_and_send_email()
        except Exception:
            print("Login UI not found, maybe already logged in.")

        start_time = time.time()
        while time.time() - start_time < 600:  # 10 minutes
            if self.is_qr_outdated():
                self.refresh_qr_code()
                time.sleep(5)  # Wait for the QR code to refresh
                self.take_screenshot_and_send_email()

            if self.is_second_verify_visible():
                if self.handle_second_verify():
                    time.sleep(3)
                    continue

            if self.is_already_logged_in():
                print("Logged in successfully, stopping checks.")
                break

            time.sleep(5)

    def is_already_logged_in(self):
        # Check for specific text that indicates we are logged in
        return bool(self.driver.find_elements(By.XPATH, "//div[text()='陈苗LazyingArt懒人艺术']"))

    def is_qr_outdated(self):
        outdated_texts = [
            "二维码已失效",
            "二维码已过期",
        ]
        for text in outdated_texts:
            if self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]"):
                return True
        return False

    def refresh_qr_code(self):
        print("QR code is outdated, attempting to refresh...")
        refresh_clicked = False
        selectors = [
            (By.XPATH, "//*[contains(text(), '点击刷新')]"),
            (By.XPATH, "//*[contains(text(), '刷新')]"),
        ]
        for by, selector in selectors:
            try:
                elements = self.driver.find_elements(by, selector)
                for element in elements:
                    if element.is_displayed():
                        element.click()
                        refresh_clicked = True
                        break
            except Exception:
                continue
            if refresh_clicked:
                break

        if refresh_clicked:
            print("Refresh click attempted.")
            return

        self.driver.refresh()
        time.sleep(2)
        self.click_login_button()
        self.click_qr_tab()
        print("Page refreshed as fallback.")

    def take_screenshot_and_send_email(self, subject=None, content=None):
        screenshot_path = '/tmp/douyin-login.png'
        self.driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}.")
        subject = subject or 'Douyin Login Required'
        content = content or 'Login is required. Please see the attached screenshot including the QR code.'
        self.mailer.send_email(
            subject,
            content,
            screenshot_path,
            'douyin-login.png'
        )

if __name__ == "__main__":
    douyin_login = DouyinLogin()
    douyin_login.check_and_act()
