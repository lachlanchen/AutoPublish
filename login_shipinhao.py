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
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from utils import QRCodeProcessor, SendMail
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
    def __init__(self, driver=None, port="5003", attention_callback=None):
        print("Initializing ShiPinHaoLogin class...")
        self.mailer = SendMail()  # Using default parameters
        self.port = port
        self.driver = driver if driver else self.create_new_driver()
        self.attention_callback = attention_callback

    def _notify_attention(self, status, artifact_path=None):
        if not self.attention_callback:
            return
        try:
            self.attention_callback(
                status=status,
                platform="shipinhao",
                kind="login_qr",
                artifact_path=artifact_path,
                message="Shipinhao login is required. Scan the current QR code.",
            )
        except Exception as exc:
            print(f"Could not update publish attention state: {exc}")

    @staticmethod
    def _login_wait_seconds():
        try:
            return max(60, int(os.environ.get("AUTOPUBLISH_LOGIN_WAIT_SECONDS", "1800")))
        except (TypeError, ValueError):
            return 1800

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
        return "channels.weixin.qq.com/login" in current_url

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

        end_time = time.time() + self._login_wait_seconds()

        while time.time() < end_time:
            if self.is_qr_outdated():
                print("QR code is outdated, refreshing...")
                self.refresh_qr_code()
                if self.is_publish_editor_ready() or self.find_lazying_art():
                    print("Logged in successfully after QR refresh.")
                    self._notify_attention("resolved")
                    break
                self.take_screenshot_and_send_email(
                    subject="Shipinhao Login Required - Refreshed QR",
                    content="The previous Shipinhao QR expired. Please scan this refreshed QR code.",
                )

            if self.needs_login():
                print("Login required, will check again in 5 seconds...")
                time.sleep(5)  # Check again in 5 seconds
            else:
                print("Logged in successfully, stopping checks.")
                self._notify_attention("resolved")
                break  # Break the loop if logged in

        if not (self.is_publish_editor_ready() or self.find_lazying_art()):
            log_html_snapshot(self.driver, "shipinhao", "login_timeout")
            raise RuntimeError("Shipinhao login required; QR login was not completed before timeout.")

        # self.driver.quit()

    def _visible_refresh_control(self):
        selectors = (
            ".js_refresh_qrcode",
            ".web_qrcode_refresh_btn",
            ".mask.show .refresh-wrap",
            ".refresh-wrap",
        )
        for selector in selectors:
            try:
                for element in self.driver.find_elements(By.CSS_SELECTOR, selector):
                    if element.is_displayed():
                        return element
            except Exception:
                continue
        return None

    def _current_context_has_outdated_qr(self):
        text_selectors = (
            ".mask.show .refresh-tip",
            ".refresh-tip",
            ".web_qrcode_msg_error",
        )
        expired_markers = ("二维码已过期", "二维码失效", "重新扫码", "刷新二维码")
        for selector in text_selectors:
            try:
                for element in self.driver.find_elements(By.CSS_SELECTOR, selector):
                    text = (element.text or "").strip()
                    if element.is_displayed() and any(marker in text for marker in expired_markers):
                        return True
            except Exception:
                continue
        return self._visible_refresh_control() is not None

    def is_qr_outdated(self):
        try:
            self.driver.switch_to.default_content()
            if self._current_context_has_outdated_qr():
                return True
            if self._switch_to_login_iframe(timeout=1):
                return self._current_context_has_outdated_qr()
            return False
        except Exception as e:
            print(f"Error checking if QR is outdated: {e}")
            return False

    def refresh_qr_code(self):
        try:
            self.driver.switch_to.default_content()
        except Exception:
            pass

        contexts = ["default"]
        if self._switch_to_login_iframe(timeout=2):
            contexts.insert(0, "iframe")

        for context in contexts:
            if context == "default":
                try:
                    self.driver.switch_to.default_content()
                except Exception:
                    pass

            control = self._visible_refresh_control()
            if control is None:
                continue

            old_sources = {
                element.get_attribute("src")
                for element in self.driver.find_elements(By.CSS_SELECTOR, "img.js_qrcode_img")
                if element.is_displayed() and element.get_attribute("src")
            }
            try:
                control.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", control)

            def qr_replaced(driver):
                new_sources = {
                    element.get_attribute("src")
                    for element in driver.find_elements(By.CSS_SELECTOR, "img.js_qrcode_img")
                    if element.is_displayed() and element.get_attribute("src")
                }
                return bool(new_sources and (not old_sources or new_sources != old_sources))

            try:
                WebDriverWait(self.driver, 20).until(qr_replaced)
                print("Shipinhao QR code refreshed with the visible refresh control.")
                return True
            except TimeoutException:
                print("Shipinhao QR refresh control did not produce a new QR in time.")
                break

        try:
            self.driver.switch_to.default_content()
        except Exception:
            pass
        print("Refreshing the Shipinhao login page as a QR refresh fallback.")
        self.driver.refresh()
        time.sleep(5)
        if not self._switch_to_login_iframe(timeout=20):
            raise RuntimeError("Shipinhao login iframe did not return after refreshing the expired QR.")
        WebDriverWait(self.driver, 20).until(
            lambda driver: any(
                element.is_displayed()
                for element in driver.find_elements(By.CSS_SELECTOR, "img.js_qrcode_img")
            )
        )
        return True

    def needs_login(self):
        if self.is_publish_editor_ready():
            return False
        if self.find_lazying_art():
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
        return True

    def _save_visible_qr_source(self, output_path):
        try:
            self.driver.switch_to.default_content()
        except Exception:
            pass
        if not self._switch_to_login_iframe(timeout=5):
            return None

        selectors = ("img.js_qrcode_img", "img.qrcode")
        for selector in selectors:
            try:
                for element in self.driver.find_elements(By.CSS_SELECTOR, selector):
                    if not element.is_displayed():
                        continue
                    source_url = element.get_attribute("src") or ""
                    parsed = urlsplit(source_url)
                    if parsed.scheme != "https" or parsed.hostname != "open.weixin.qq.com":
                        continue
                    request = Request(
                        source_url,
                        headers={
                            "User-Agent": "Mozilla/5.0",
                            "Referer": "https://open.weixin.qq.com/",
                        },
                    )
                    with urlopen(request, timeout=20) as response:
                        data = response.read(2 * 1024 * 1024 + 1)
                    if not data or len(data) > 2 * 1024 * 1024:
                        continue
                    Path(output_path).write_bytes(data)
                    return output_path
            except Exception:
                continue
        return None

    def take_screenshot_and_send_email(self, subject=None, content=None):
        screenshot_path = '/tmp/shipinhao-screenshot.png'
        try:
            self.driver.switch_to.default_content()
        except Exception:
            pass
        self.driver.save_screenshot(screenshot_path)
        qr_source_path = self._save_visible_qr_source('/tmp/shipinhao-qr-source.jpg')
        qr_source_path = qr_source_path or screenshot_path
        qr_path = None
        try:
            qr_path = QRCodeProcessor.build_watch_friendly_png(qr_source_path)
            self._notify_attention("required", qr_path)
        except Exception as exc:
            print(f"Could not prepare job-scoped Shipinhao QR artifact: {exc}")
        try:
            email_path = qr_path or qr_source_path
            sent = self.mailer.send_email(
                subject or 'Shipinhao Login Required',
                content or 'Login is required. Please scan the attached QR code.',
                email_path,
                'shipinhao-login-qr.png'
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
