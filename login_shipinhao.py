from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment
# from sendgrid.helpers.mail import FileContent, FileName, FileType, Disposition
import time
import os
import base64
import traceback

from utils import SendMail
from utils import dismiss_alert, bring_to_front, log_html_snapshot

# class SendMail:
#     # Set defaults within the class, but allow them to be overridden
#     def __init__(self, sendgrid_api_key=os.environ.get('SENDGRID_API_KEY'), from_email=os.environ.get('FROM_EMAIL'), to_email=os.environ.get('TO_EMAIL')):
#         self.sendgrid_api_key = sendgrid_api_key
#         self.from_email = from_email
#         self.to_email = to_email

#     def send_email(self, subject, content, attachment_path, attachment_name):
#         sg = SendGridAPIClient(self.sendgrid_api_key)
#         mail = Mail(
#             from_email=Email(self.from_email),
#             to_emails=To(self.to_email),
#             subject=subject,
#             plain_text_content=content
#         )

#         with open(attachment_path, 'rb') as f:
#             data = f.read()
#             encoded_file = base64.b64encode(data).decode()

#         attachment = Attachment()
#         attachment.file_content = FileContent(encoded_file)
#         attachment.file_type = FileType('image/png')
#         attachment.file_name = FileName(attachment_name)
#         attachment.disposition = Disposition('attachment')
#         mail.add_attachment(attachment)

#         response = sg.send(mail)
#         print(f"Email sent, status code: {response.status_code}")

class ShiPinHaoLogin:
    def __init__(self, driver=None, port="5003"):
        print("Initializing ShiPinHaoLogin class...")
        self.mailer = SendMail()  # Using default parameters
        self.port = port
        self.driver = driver if driver else self.create_new_driver()

    def create_new_driver(self):
        print("Creating new WebDriver instance...")
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.port}")
        driver = webdriver.Chrome(options=options)
        return driver

    def is_login_iframe_present(self):
        try:
            self.driver.switch_to.default_content()
        except Exception:
            pass
        iframe_selectors = [
            "iframe.display",
            "#wx-oauth-container iframe",
            "iframe[src*='login-for-iframe']",
            "iframe[src*='open.weixin.qq.com/connect/qrconnect']",
            "iframe[src*='qrconnect']",
        ]
        for selector in iframe_selectors:
            try:
                for iframe in self.driver.find_elements(By.CSS_SELECTOR, selector):
                    src = iframe.get_attribute("src") or ""
                    if (
                        "login-for-iframe" in src
                        or "open.weixin.qq.com/connect/qrconnect" in src
                        or "qrconnect" in src
                        or selector == "#wx-oauth-container iframe"
                    ):
                        print(f"Login QR iframe detected with selector {selector}.")
                        return True
            except Exception:
                continue
        try:
            page_source = self.driver.page_source or ""
            if self._page_source_has_login_qr(page_source):
                print("Shipinhao login QR markers detected in page source.")
                return True
        except Exception:
            return False
        return False

    @staticmethod
    def _page_source_has_login_qr(page_source):
        markers = (
            "login-for-iframe",
            "open.weixin.qq.com/connect/qrconnect",
            "wx-oauth-container",
            "login-qrcode-wrap",
            "qrcode-area",
            "qrcode-tip",
            "登录视频号助手",
            "微信扫码登录",
            "视频号助手",
        )
        return any(marker in (page_source or "") for marker in markers)

    def _looks_like_login_page(self):
        try:
            self.driver.switch_to.default_content()
        except Exception:
            pass
        try:
            page_source = self.driver.page_source or ""
        except Exception:
            page_source = ""
        if self._page_source_has_login_qr(page_source):
            return True
        try:
            current_url = self.driver.current_url or ""
            title = self.driver.title or ""
        except Exception:
            current_url = ""
            title = ""
        return "channels.weixin.qq.com/login" in current_url or "视频号助手" in title

    def _switch_to_login_iframe(self, timeout=20):
        try:
            self.driver.switch_to.default_content()
        except Exception:
            pass
        locators = [
            (By.CSS_SELECTOR, "iframe.display"),
            (By.CSS_SELECTOR, "#wx-oauth-container iframe"),
            (By.CSS_SELECTOR, "iframe[src*='login-for-iframe']"),
            (By.CSS_SELECTOR, "iframe[src*='open.weixin.qq.com/connect/qrconnect']"),
            (By.CSS_SELECTOR, "iframe[src*='qrconnect']"),
            (By.XPATH, "//iframe[contains(@src, 'login-for-iframe') or contains(@src, 'open.weixin.qq.com/connect/qrconnect') or contains(@src, 'qrconnect')]"),
        ]
        per_locator_timeout = max(1, timeout / max(len(locators), 1))
        for by, selector in locators:
            try:
                self.driver.switch_to.default_content()
            except Exception:
                pass
            try:
                WebDriverWait(self.driver, per_locator_timeout).until(
                    EC.frame_to_be_available_and_switch_to_it((by, selector))
                )
                print(f"Switched to Shipinhao login iframe with selector: {selector}")
                return True
            except TimeoutException:
                continue
        try:
            self.driver.switch_to.default_content()
        except Exception:
            pass
        return False

    def _click_login_retry_if_visible(self):
        try:
            self.driver.switch_to.default_content()
        except Exception:
            pass
        retry_selectors = [
            ".mask.show .refresh-wrap",
            ".mask .refresh-wrap",
            ".refresh-wrap",
        ]
        for selector in retry_selectors:
            try:
                for element in self.driver.find_elements(By.CSS_SELECTOR, selector):
                    text = element.text or ""
                    if element.is_displayed() and ("加载失败" in text or "二维码已过期" in text or "重试" in text):
                        print(f"Clicking Shipinhao login QR retry control: {text.strip()}")
                        element.click()
                        time.sleep(3)
                        return True
            except Exception:
                continue
        return False

    def is_publish_editor_ready(self):
        try:
            self.driver.switch_to.default_content()
        except Exception:
            pass

        if self.is_login_iframe_present():
            return False

        selectors = [
            "input[type='file'][accept*='video']",
            ".post-create-wrap",
            ".post-edit-wrap",
            ".form-btns",
        ]
        for selector in selectors:
            try:
                for element in self.driver.find_elements(By.CSS_SELECTOR, selector):
                    if element.is_displayed():
                        print(f"Shipinhao editor detected with selector: {selector}")
                        return True
            except Exception:
                continue

        try:
            page_text = self.driver.page_source or ""
        except Exception:
            page_text = ""
        editor_markers = ("视频描述", "发表动态", "保存草稿", "封面预览", "手机预览")
        if any(marker in page_text for marker in editor_markers):
            print("Shipinhao editor text detected; treating session as logged in.")
            return True
        return False

    # def find_lazying_art(self):
    #     try:
    #         # Search for the span element containing the specific text
    #         # Adjusted the XPath to target the class and text more accurately based on the provided structure
    #         user_info_element = self.driver.find_element(By.XPATH, "//span[contains(@class, 'name') and contains(text(), '陈苗LazyingArt懒人艺术')]")
    #         if user_info_element:
    #             print("Found '陈苗LazyingArt懒人艺术'.")
    #             return True
    #     except NoSuchElementException:
    #         # If the element is not found, NoSuchElementException is caught
    #         print("Did not find '陈苗LazyingArt懒人艺术'.")
    #     return False
    def _expected_account_names(self):
        env_names = os.environ.get("SHIPINHAO_ACCOUNT_NAMES") or os.environ.get("SHIPINHAO_ACCOUNT_NAME")
        if env_names:
            return [name.strip() for name in env_names.split(",") if name.strip()]
        return [
            "LazyingArt懒人艺术",
            "LazyingArt懶人藝術",
            "陈苗LazyingArt懒人艺术",
            "LazyingArt",
            "陈苗",
            "懒人艺术",
            "懶人藝術",
        ]

    def find_lazying_art(self):
        try:
            # First switch to default content in case we're in an iframe
            try:
                self.driver.switch_to.default_content()
            except Exception as e:
                print(f"Error switching to default content: {e}")

            if self.is_login_iframe_present():
                print("Login iframe is present; not logged in yet.")
                return False
                
            # Try multiple selector strategies for better reliability
            selectors = [
                # Original approach - specific class and text
                "//span[contains(@class, 'name') and contains(text(), 'LazyingArt懒人艺术')]",
                "//span[contains(@class, 'name') and contains(text(), '陈苗LazyingArt懒人艺术')]",
                # More flexible - just look for the class with partial text
                "//span[contains(@class, 'name') and contains(text(), 'LazyingArt')]",
                "//span[contains(@class, 'name') and contains(text(), '陈苗LazyingArt')]",
                # Even more flexible - any element with account info near it
                "//div[contains(@class, 'account-info')]//span[contains(text(), 'LazyingArt')]",
                "//div[contains(@class, 'account-info')]//span[contains(text(), '陈苗')]",
                # Try CSS selector approach
                ".account-info .name"
            ]

            expected_names = self._expected_account_names()
            for selector in selectors:
                try:
                    wait = WebDriverWait(self.driver, 5)
                    if selector.startswith('.'):
                        elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
                    else:
                        elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, selector)))
                    
                    for element in elements:
                        text = (element.text or "").strip()
                        if not text:
                            continue
                        if any(name in text for name in expected_names):
                            print(f"Found user element with text: '{element.text}' using selector: {selector}")
                            return True
                        if selector == ".account-info .name":
                            print(f"Found account name element without match: '{text}'. Treating as logged in.")
                            return True
                except Exception as e:
                    print(f"Selector {selector} failed: {e}")
                    continue
                    
            # Take a screenshot for debugging
            debug_path = '/tmp/debug-screenshot.png'
            self.driver.save_screenshot(debug_path)
            print(f"Saved debug screenshot to {debug_path}")
            log_html_snapshot(self.driver, "shipinhao", "login_check")
            
            print(f"Did not find any expected Shipinhao account names: {expected_names}")
            return False
        except Exception as e:
            print(f"Error in find_lazying_art: {e}")
            traceback.print_exc()
            return False


    def check_and_act(self):
        print("Navigating to the URL...")
        bring_to_front(["视频号"])

        url = 'https://channels.weixin.qq.com/platform/post/create'
        self.driver.get(url)

        time.sleep(1)

        dismiss_alert(self.driver)

        time.sleep(3)

        bring_to_front(["视频号"])

        if self.is_publish_editor_ready() or self.find_lazying_art():
            print("Already logged in. ")
            return

        if self.is_login_iframe_present():
            log_html_snapshot(self.driver, "shipinhao", "login_required")

        self._click_login_retry_if_visible()

        if self._looks_like_login_page():
            print("Shipinhao login page is visible; sending full-page QR screenshot.")
            try:
                self.driver.switch_to.default_content()
            except Exception:
                pass
            self.take_screenshot_and_send_email()
        elif self._switch_to_login_iframe(timeout=20):
            self.take_screenshot_and_send_email()
        elif self._looks_like_login_page():
            print("Shipinhao login page is visible after iframe wait; sending full-page QR screenshot.")
            try:
                self.driver.switch_to.default_content()
            except Exception:
                pass
            self.take_screenshot_and_send_email()
        elif self.is_publish_editor_ready() or self.find_lazying_art():
            print("Logged in while waiting for login iframe.")
            return
        else:
            log_html_snapshot(self.driver, "shipinhao", "login_iframe_missing")
            raise RuntimeError("Shipinhao login iframe was not available and the publish editor is not ready.")

        end_time = time.time() + 1800  # 30 minutes from now
        last_refresh_time = time.time()
        last_email_time = time.time() - 30  # Initialize to send email immediately

        while time.time() < end_time:
            current_time = time.time()
        
            # if self.is_qr_outdated() or (current_time - last_refresh_time >= 180):
            if self.is_qr_outdated():
                print("QR code is outdated, refreshing...")
                try:
                    self.driver.switch_to.default_content()
                except Exception:
                    pass
                self.driver.refresh()
                time.sleep(5)
                if self.is_publish_editor_ready() or self.find_lazying_art():
                    print("Logged in successfully after QR refresh.")
                    break
                if self._switch_to_login_iframe(timeout=20):
                    self.take_screenshot_and_send_email()
                else:
                    print("Login iframe disappeared after QR refresh; rechecking login state instead of failing.")
                    log_html_snapshot(self.driver, "shipinhao", "login_iframe_after_refresh_missing")
                    time.sleep(5)
                    continue
                last_refresh_time = time.time()

            # if time.time() - last_email_time >= 60:  # Take screenshot and send email every 60 seconds
            #     print("Taking screenshot and sending email...")
            #     self.take_screenshot_and_send_email()
            #     last_email_time = time.time()

            if self.needs_login():
                print("Login required, will check again in 5 seconds...")
                time.sleep(5)  # Check again in 5 seconds
            else:
                print("Logged in successfully, stopping checks.")
                break  # Break the loop if logged in

        if not (self.is_publish_editor_ready() or self.find_lazying_art()):
            log_html_snapshot(self.driver, "shipinhao", "login_timeout")
            raise RuntimeError("Shipinhao login required; QR login was not completed before timeout.")

        # self.driver.quit()

    # def is_qr_outdated(self):
    #     elements = self.driver.find_elements(By.CSS_SELECTOR, ".refresh-wrap .refresh-tip")
    #     for element in elements:
    #         if element.text == "二维码已过期，点击刷新":
    #             return True
    #     return False
    def is_qr_outdated(self):
        try:
            self._switch_to_login_iframe(timeout=1)
            # Look for the more specific structure - a visible mask containing the refresh message
            elements = self.driver.find_elements(By.CSS_SELECTOR, ".mask.show .refresh-tip")
            for element in elements:
                if "二维码已过期" in element.text:
                    return True
                    
            # Alternative approach - check if the mask with refresh is visible
            outdated_masks = self.driver.find_elements(By.CSS_SELECTOR, ".mask.show")
            for mask in outdated_masks:
                refresh_tips = mask.find_elements(By.CSS_SELECTOR, ".refresh-tip")
                for tip in refresh_tips:
                    if "二维码已过期" in tip.text:
                        return True
                        
            return False
        except Exception as e:
            print(f"Error checking if QR is outdated: {e}")
            return False

    def needs_login(self):
        if self.is_publish_editor_ready():
            return False
        if self._looks_like_login_page():
            return True
        if self._switch_to_login_iframe(timeout=1):
            elements = self.driver.find_elements(By.CSS_SELECTOR, ".tip span")
            for element in elements:
                if element.text == "微信扫码登录 视频号助手":
                    return True
            try:
                self.driver.switch_to.default_content()
            except Exception:
                pass

        if self.find_lazying_art():
            return False
        else:
            return True

    def take_screenshot_and_send_email(self):
        screenshot_path = '/tmp/shipinhao-screenshot.png'
        self.driver.save_screenshot(screenshot_path)
        try:
            sent = self.mailer.send_email(
                'Shipinhao Login Required',
                'Login is required. Please see the attached screenshot.',
                screenshot_path,
                'shipinhao-screenshot.png'
            )
            if not sent:
                print("Login email was not sent (SMTP not configured or authentication failed).")
        except Exception as exc:
            print(f"Failed to send login email: {exc}")
            traceback.print_exc()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="5006", help="Chrome debugging port")
    args = parser.parse_args()

    shi_pin_hao_login = ShiPinHaoLogin(port=args.port)
    shi_pin_hao_login.check_and_act()
