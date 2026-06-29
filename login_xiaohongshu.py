from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
import base64

from utils import SendMail
from utils import dismiss_alert, bring_to_front

class XiaoHongShuLogin:
    def __init__(self, driver=None, port="5003"):
        print("Initializing XiaoHongShuLogin class...")
        self.mailer = SendMail(
            sendgrid_api_key=None,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
        )
        self.port = port
        self.driver = driver if driver else self.create_new_driver()
        self.refresh_count = 0

    def _login_wait_seconds(self):
        try:
            return max(60, int(os.environ.get("AUTOPUBLISH_LOGIN_WAIT_SECONDS", "1800")))
        except Exception:
            return 1800

    def create_new_driver(self):
        print("Creating new WebDriver instance...")
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.port}")
        driver = webdriver.Chrome(options=options)
        return driver

    def show_qr(self):
        """Attempt to reveal the QR code directly using WebDriver with a structural-based approach."""
        try:
            # Wait for the container to ensure the page has loaded
            WebDriverWait(self.driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.login-box-container')))
            # Use XPath to navigate to the QR button based on structure
            qr_button_xpath = "//div[contains(@class, 'login-box-container')]//img[contains(@src, 'data:image/png;base64')]"
            qr_button = self.driver.find_element(By.XPATH, qr_button_xpath)
            qr_button.click()
            print("QR code reveal attempted using WebDriver.")
        except Exception as e:
            print(f"Attempting to reveal QR code using JavaScript due to failure: {e}")
            self.show_qr_with_js()



    def show_qr_with_js(self):
        """Attempt to reveal the QR code using JavaScript with a structural-based approach."""
        qr_reveal_script = """
        var qrButtons = document.querySelectorAll("div.login-box-container img[src*='data:image/png;base64']");
        if (qrButtons.length > 0) {
            qrButtons[0].click();  // Assuming the first found QR button is the correct one
        } else {
            console.error('QR reveal button not found using JavaScript.');
        }
        """
        try:
            self.driver.execute_script(qr_reveal_script)
            print("Attempted to reveal QR code using JavaScript.")
        except Exception as e:
            print(f"Failed to reveal QR code using JavaScript: {e}")

    def _expected_account_names(self):
        env_names = os.environ.get("XHS_ACCOUNT_NAMES") or os.environ.get("XHS_ACCOUNT_NAME")
        if env_names:
            return [name.strip() for name in env_names.split(",") if name.strip()]
        return [
            "LazyingArt懒人艺术",
            "LazyingArt懶人藝術",
            "陈苗LazyingArt懒人艺术",
            "陈苗LazyingArt",
            "懒人艺术",
            "懶人藝術",
        ]

    def find_lazying_art(self):
        expected_names = self._expected_account_names()
        selectors = [
            (By.CSS_SELECTOR, "span"),
            (By.CSS_SELECTOR, ".user-name"),
            (By.CSS_SELECTOR, ".name"),
            (By.XPATH, "//*[self::span or self::div][normalize-space(text())]"),
        ]

        for by, selector in selectors:
            try:
                elements = self.driver.find_elements(by, selector)
            except Exception:
                continue
            for element in elements:
                text = (element.text or "").strip()
                if not text:
                    continue
                if any(name in text for name in expected_names):
                    print(f"Found account name '{text}'.")
                    return True

        print(f"Did not find any expected XHS account names: {expected_names}")
        return False

    def _has_login_box(self):
        try:
            boxes = self.driver.find_elements(By.CSS_SELECTOR, "div.login-box-container")
        except Exception:
            return False
        return any(box.is_displayed() for box in boxes)

    def is_already_logged_in(self):
        if self.find_lazying_art():
            return True
        try:
            current_url = self.driver.current_url or ""
            body_text = self.driver.execute_script(
                "return document.body ? document.body.innerText.slice(0, 5000) : '';"
            )
        except Exception:
            current_url = ""
            body_text = ""

        logged_in_path = "creator.xiaohongshu.com/creator" in current_url
        logged_in_markers = [
            "发布笔记",
            "发布视频",
            "创作服务",
            "数据中心",
            "内容管理",
            "创作者中心",
        ]
        if logged_in_path and not self._has_login_box() and any(text in body_text for text in logged_in_markers):
            print(f"XiaoHongShu creator page detected as logged in: {current_url}")
            return True
        return False


    def check_and_act(self):
        print("Navigating to the XiaoHongShu login page...")

        bring_to_front(["小红书", "你访问的页面不见了"])

        url = 'https://creator.xiaohongshu.com/creator/home'
        self.driver.get(url)



        time.sleep(1)

        dismiss_alert(self.driver)

        time.sleep(3)

        bring_to_front(["小红书", "你访问的页面不见了"])

        if self.is_already_logged_in():
            print("Already logged in. ")
            return True


        try:
            WebDriverWait(self.driver, 30).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.login-box-container')))
            

            # # Click on the top right corner of the SMS login box to reveal the QR code
            # qr_button = self.driver.find_element(By.CSS_SELECTOR, 'img.css-wemwzq')
            # ActionChains(self.driver).click(qr_button).perform()

            self.show_qr()

            # Wait a few seconds for the QR code to be fully loaded and visible
            time.sleep(5)  # Adjust timing based on actual page behavior

            self.take_screenshot_and_send_email()
            
        except TimeoutException:
            if self.is_already_logged_in():
                print("Already logged in or the page did not load as expected.")
                return True
            self.take_screenshot_and_send_email(
                subject="XiaoHongShu Login Page Changed",
                content="XiaoHongShu login is required, but the expected QR login box was not found. Please inspect the attached screenshot.",
            )
            raise RuntimeError("XiaoHongShu login box was not found.")

        wait_seconds = self._login_wait_seconds()
        end_time = time.time() + wait_seconds
        last_refresh_time = time.time()
        last_email_time = time.time() - 30  # Initialize to send email immediately

        while time.time() < end_time:
            if self.is_qr_outdated():
                print("QR code is outdated, attempting to refresh...")
                # self.refresh_qr_code()
                # self.driver.refresh()
                self.refresh_qr_code()
                time.sleep(5)
                self.take_screenshot_and_send_email()
                last_refresh_time = time.time()

            # if time.time() - last_email_time >= 60:  # Take screenshot and send email every 60 seconds
            #     print("Taking screenshot and sending email...")
            #     time.sleep(3)
            #     self.take_screenshot_and_send_email()
            #     last_email_time = time.time()

            if self.is_already_logged_in() or not self.needs_login():
                print("Logged in successfully, stopping checks.")
                return True

            time.sleep(5)  # Wait for 5 seconds before checking again

        raise RuntimeError(f"XiaoHongShu login was not completed within {wait_seconds} seconds.")

    def is_qr_outdated(self):
        outdated_message = "二维码已失效，请刷新"
        return bool(self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{outdated_message}')]"))

    def refresh_qr_code(self):
        try:
            if self.refresh_count % 2:
                raise Exception("Default method failed in last attempt. ")

            # Locate the refresh button by its text and click it using JavaScript
            refresh_button_script = """
            var buttons = document.querySelectorAll('button');
            var buttonClicked = false;
            for (var i = 0; i < buttons.length; i++) {
                if (buttons[i].querySelector('span.btn-content') && buttons[i].querySelector('span.btn-content').textContent.trim() === '刷新') {
                    buttons[i].click();
                    buttonClicked = true;
                    break;
                }
            }
            return buttonClicked;
            """

            # Execute the script
            buttonClicked = self.driver.execute_script(refresh_button_script)

            # Check if the button was clicked successfully
            if buttonClicked:
                print("QR code refreshed successfully.")
                self.refresh_count += 1
            else:
                print("Refresh button not found.")
                raise Exception("Refresh button not found. ")

            

        except Exception as e:
            print(f"Direct refresh failed, attempting alternative method: {e}")
            # If clicking the refresh button fails, refresh the page
            self.driver.refresh()
            # Wait for the login box to become visible again
            WebDriverWait(self.driver, 30).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.login-box-container')))
            
            self.show_qr()

            self.refresh_count = 0
            
    def needs_login(self):
        if self._has_login_box():
            print("SMS login box detected, login is required.")
            return True
        print("No SMS login box detected, might already be logged in or the page did not load as expected.")
        return False

    def take_screenshot_and_send_email(self, subject=None, content=None):
        screenshot_path = '/tmp/xiaohongshu-login.png'
        self.driver.save_screenshot(screenshot_path)
        self.mailer.send_email(
            subject or 'XiaoHongShu Login Required',
            content or 'Login is required. Please see the attached screenshot including the QR code.',
            screenshot_path,
            'xiaohongshu-login.png'
        )

if __name__ == "__main__":
    xhs_login = XiaoHongShuLogin()
    xhs_login.check_and_act()
