import pathlib
import email
import imaplib
import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, NoSuchWindowException, TimeoutException

from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager

from utils import dismiss_alert, crop_and_resize_cover_image, bring_to_front, close_extra_tabs, safe_get, log_html_snapshot, SendMail
from login_bilibili import BilibiliLogin

import traceback

import time
import os
import shutil
import tempfile
import requests
import base64
import os
import json
from urllib.parse import quote


from selenium.common.exceptions import NoAlertPresentException
from PIL import Image
from datetime import datetime, timezone
from email.header import decode_header
from email.utils import parsedate_to_datetime


def download_image(url, local_path='./temp/'):
    response = requests.get(url)
    if response.status_code == 200:
        os.makedirs(local_path, exist_ok=True)
        filename = url.split('/')[-1].split('?')[0]
        file_path = os.path.join(local_path, filename)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        return file_path, 0
    else:
        raise Exception(f"Error downloading image: Status code {response.status_code}")

# Function to call the API with base64 encoded image
def b64_api(username, password, img_path, ID):
    with open(img_path, 'rb') as f:
        b64_data = base64.b64encode(f.read())
    b64 = b64_data.decode()
    data = {"username": username, "password": password, "ID": ID, "b64": b64, "version": "3.1.1"}
    data_json = json.dumps(data)
    result = json.loads(requests.post("http://www.fdyscloud.com.cn/tuling/predict", data=data_json).text)

    # Save the result to a JSON file with the same base name as the image file
    base_name = os.path.splitext(os.path.basename(img_path))[0]  # Extracts filename without extension
    json_path = os.path.join(os.path.dirname(img_path), base_name + '.json')
    
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(result, json_file, ensure_ascii=False, indent=4)

    return result


class BilibiliRateLimitException(Exception):
    pass


class BilibiliSmsVerificationRequired(Exception):
    pass


class BilibiliPublisher:
    def __init__(self, driver, path_mp4, path_cover, metadata, test=False):
        self.driver = driver
        self.path_mp4 = path_mp4
        self.path_cover = path_cover
        self.metadata = metadata
        self.test = test
        self.retry_count = 0  # initialize retry count
        self.mailer = SendMail()

        bilibili_login = BilibiliLogin(driver)
        bilibili_login.check_and_act()

    def wait_for_element_to_be_clickable(self, xpath, timeout=600):
        time.sleep(3)  # your actual implementation

    def _find_visible(self, xpaths):
        for xpath in xpaths:
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
            except Exception:
                continue
            for element in elements:
                try:
                    if element.is_displayed():
                        return element, xpath
                except Exception:
                    continue
        return None, None

    def _safe_click(self, element):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        except Exception:
            pass
        try:
            element.click()
            return True
        except Exception:
            try:
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except Exception:
                return False

    def _click_first_visible(self, css_selectors=None, xpaths=None, label="element"):
        css_selectors = css_selectors or []
        xpaths = xpaths or []
        for selector in css_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            except Exception:
                continue
            for element in elements:
                try:
                    if element.is_displayed() and self._safe_click(element):
                        print(f"Clicked Bilibili {label}: {selector}")
                        return True
                except Exception:
                    continue
        for xpath in xpaths:
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
            except Exception:
                continue
            for element in elements:
                try:
                    if element.is_displayed() and self._safe_click(element):
                        print(f"Clicked Bilibili {label}: {xpath}")
                        return True
                except Exception:
                    continue
        return False

    def _close_optional_upload_overlays(self):
        closed = False
        # Older Bilibili flows sometimes asked for a dismissible SMS prompt only
        # for completion notifications. Newer flows can require SMS before the
        # upload leaves 0%, so the upload loop also checks for that hard gate.
        closed |= self._click_first_visible(
            css_selectors=[".base-verify-close"],
            label="optional SMS verification close",
        )
        time.sleep(0.5 if closed else 0)
        closed |= self._click_first_visible(
            css_selectors=[".bcc-dialog__close"],
            xpaths=['//*[normalize-space()="知道了"]'],
            label="notification dialog close",
        )
        return closed

    def _sms_verification_text(self):
        try:
            text = self.driver.execute_script("return document.body ? document.body.innerText : '';") or ""
        except Exception:
            return ""
        markers = ("请完成短信验证", "获取验证码")
        if all(marker in text for marker in markers):
            return "Bilibili SMS verification required before upload can continue."
        return ""

    def _decode_mail_header(self, value):
        if not value:
            return ""
        pieces = []
        for chunk, encoding in decode_header(value):
            if isinstance(chunk, bytes):
                pieces.append(chunk.decode(encoding or "utf-8", errors="replace"))
            else:
                pieces.append(chunk)
        return "".join(pieces)

    def _mail_text(self, message):
        if message.is_multipart():
            parts = []
            for part in message.walk():
                content_type = part.get_content_type()
                disposition = (part.get("Content-Disposition") or "").lower()
                if "attachment" in disposition or content_type not in ("text/plain", "text/html"):
                    continue
                payload = part.get_payload(decode=True)
                if not payload:
                    continue
                charset = part.get_content_charset() or "utf-8"
                parts.append(payload.decode(charset, errors="replace"))
            return "\n".join(parts)
        payload = message.get_payload(decode=True)
        if not payload:
            return ""
        charset = message.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")

    def _extract_verification_code(self, text):
        if not text:
            return None
        patterns = [
            r"(?:验证码|校验码|verification\s*code|code)\D{0,12}(\d{4,8})(?!\d)",
            r"(?<!\d)(\d{6})(?!\d)",
            r"(?<!\d)(\d{4})(?!\d)",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                code = match.group(1)
                if code.startswith("202") and len(code) == 4:
                    continue
                return code
        return None

    def _message_timestamp(self, message):
        try:
            parsed = parsedate_to_datetime(message.get("Date"))
            if parsed is None:
                return None
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.timestamp()
        except Exception:
            return None

    def _poll_email_for_sms_code(self, request_time, timeout=None):
        from_email = os.environ.get("FROM_EMAIL")
        app_password = os.environ.get("APP_PASSWORD")
        to_email = os.environ.get("TO_EMAIL", "")
        if not from_email or not app_password:
            raise BilibiliSmsVerificationRequired(
                "Bilibili SMS verification email was sent, but IMAP polling is not configured. "
                "Set FROM_EMAIL and APP_PASSWORD or paste the SMS code manually."
            )

        try:
            timeout = timeout or int(os.environ.get("AUTOPUB_BILIBILI_SMS_EMAIL_WAIT_SECONDS", "900"))
        except Exception:
            timeout = 900
        try:
            poll_seconds = max(5, int(os.environ.get("AUTOPUB_BILIBILI_SMS_EMAIL_POLL_SECONDS", "10")))
        except Exception:
            poll_seconds = 10

        deadline = time.time() + timeout
        since = datetime.fromtimestamp(request_time).strftime("%d-%b-%Y")
        seen_ids = set()
        print(f"Polling mailbox for Bilibili SMS verification reply for up to {timeout} seconds.")

        while time.time() < deadline:
            try:
                with imaplib.IMAP4_SSL(os.environ.get("AUTOPUB_IMAP_HOST", "imap.gmail.com")) as mailbox:
                    mailbox.login(from_email, app_password)
                    mailbox.select(os.environ.get("AUTOPUB_IMAP_MAILBOX", "INBOX"))
                    status, data = mailbox.search(None, "SINCE", since)
                    if status != "OK":
                        print(f"IMAP search returned {status}; retrying.")
                        time.sleep(poll_seconds)
                        continue
                    ids = (data[0] or b"").split()
                    for message_id in reversed(ids[-40:]):
                        if message_id in seen_ids:
                            continue
                        status, payload = mailbox.fetch(message_id, "(RFC822)")
                        if status != "OK" or not payload or not payload[0]:
                            continue
                        seen_ids.add(message_id)
                        message = email.message_from_bytes(payload[0][1])
                        msg_ts = self._message_timestamp(message)
                        if msg_ts is not None and msg_ts < request_time - 60:
                            continue
                        sender = self._decode_mail_header(message.get("From", ""))
                        subject = self._decode_mail_header(message.get("Subject", ""))
                        body = self._mail_text(message)
                        marker_text = f"{sender}\n{subject}\n{body}"
                        likely_reply = (
                            "bilibili" in marker_text.lower()
                            or "哔哩" in marker_text
                            or "B站" in marker_text
                            or (to_email and to_email.lower() in sender.lower())
                        )
                        if not likely_reply:
                            continue
                        code = self._extract_verification_code(body) or self._extract_verification_code(subject)
                        if code:
                            print(f"Found Bilibili SMS verification code in email reply ({len(code)} digits).")
                            return code
            except Exception as exc:
                print(f"IMAP polling failed; retrying: {exc}")
            time.sleep(poll_seconds)

        raise BilibiliSmsVerificationRequired(
            "Timed out waiting for Bilibili SMS verification code email reply."
        )

    def _click_sms_get_code(self):
        return self._click_first_visible(
            xpaths=[
                '//button[contains(normalize-space(.),"获取验证码")]',
                '//*[contains(normalize-space(.),"获取验证码")]',
                '//button[contains(normalize-space(.),"发送验证码")]',
                '//*[contains(normalize-space(.),"发送验证码")]',
                '//button[contains(normalize-space(.),"重新获取")]',
                '//*[contains(normalize-space(.),"重新获取")]',
            ],
            label="SMS get-code button",
        )

    def _send_sms_verification_email(self, upload_mp4):
        screenshot_path = "/tmp/bilibili-sms-verification.png"
        try:
            self.driver.save_screenshot(screenshot_path)
        except Exception as exc:
            print(f"Could not save Bilibili SMS screenshot: {exc}")
            Image.new("RGB", (640, 360), "white").save(screenshot_path)
        basename = os.path.basename(upload_mp4 or self.path_mp4 or "video")
        content = (
            "Bilibili is asking for an SMS verification code before publishing can continue.\n"
            f"Video: {basename}\n\n"
            "Please reply to this email with only the verification code. "
            "AutoPublish will read the reply and submit it."
        )
        sent = self.mailer.send_email(
            "Bilibili SMS Verification Code Required",
            content,
            screenshot_path,
            "bilibili-sms-verification.png",
        )
        if not sent:
            raise BilibiliSmsVerificationRequired(
                "Bilibili SMS verification is required, but AutoPublish could not send the email request."
            )

    def _fill_sms_verification_code(self, code):
        inputs = self.driver.find_elements(
            By.XPATH,
            '//input[contains(@placeholder,"验证码") or contains(@aria-label,"验证码") or contains(@name,"code")]',
        )
        if not inputs:
            inputs = self.driver.find_elements(By.XPATH, '//input[not(@type="hidden")]')
        for element in inputs:
            try:
                if not element.is_displayed() or not element.is_enabled():
                    continue
                element.clear()
                element.send_keys(code)
                print("Filled Bilibili SMS verification code.")
                break
            except Exception:
                continue
        else:
            raise BilibiliSmsVerificationRequired("Could not find a visible Bilibili SMS code input.")

        self._click_first_visible(
            xpaths=[
                '//button[contains(normalize-space(.),"确认") and not(contains(normalize-space(.),"获取"))]',
                '//button[contains(normalize-space(.),"确定") and not(contains(normalize-space(.),"获取"))]',
                '//button[contains(normalize-space(.),"验证") and not(contains(normalize-space(.),"获取"))]',
                '//*[self::div or self::span][normalize-space()="确认"]',
                '//*[self::div or self::span][normalize-space()="确定"]',
            ],
            label="SMS verification submit",
        )

    def _handle_sms_verification_gate(self, upload_mp4):
        print("Bilibili hard SMS verification gate detected.")
        if not self._click_sms_get_code():
            log_html_snapshot(self.driver, "bilibili", "sms_get_code_missing")
            raise BilibiliSmsVerificationRequired(
                "Bilibili SMS verification is required, but the get-code button was not found."
            )
        request_time = time.time()
        time.sleep(2)
        self._send_sms_verification_email(upload_mp4)
        code = self._poll_email_for_sms_code(request_time)
        self._fill_sms_verification_code(code)
        time.sleep(5)
        if self._sms_verification_text():
            raise BilibiliSmsVerificationRequired("Bilibili SMS verification is still visible after submitting the code.")
        print("Bilibili SMS verification completed.")

    def _resume_upload_if_paused(self):
        return self._click_first_visible(
            xpaths=[
                '//*[normalize-space()="继续上传"]',
                '//*[contains(normalize-space(),"继续上传")]',
            ],
            label="continue upload",
        )

    def _upload_failure_visible(self):
        failure_xpaths = [
            '//*[normalize-space()="上传失败"]',
            '//*[contains(normalize-space(),"上传失败")]',
        ]
        for xpath in failure_xpaths:
            for element in self.driver.find_elements(By.XPATH, xpath):
                try:
                    if element.is_displayed():
                        return True
                except Exception:
                    continue
        return False

    def _reset_upload_page(self):
        upload_url = f"https://member.bilibili.com/platform/upload/video/frame?autopub_ts={int(time.time())}"
        try:
            self.driver.get("about:blank")
            time.sleep(1)
        except Exception:
            pass
        safe_get(self.driver, upload_url, timeout=45, label="Bilibili upload page")

    def _current_upload_status_text(self, path_mp4):
        basename = os.path.basename(path_mp4)
        stem = os.path.splitext(basename)[0]
        return self.driver.execute_script(
            """
            const names = arguments[0];
            const rows = [];
            const isVisible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            for (const el of document.querySelectorAll('*')) {
              const ownText = (el.textContent || '').trim();
              if (!isVisible(el) || !names.some((name) => ownText.includes(name))) continue;
              let node = el;
              for (let depth = 0; node && depth < 8; depth++, node = node.parentElement) {
                const text = (node.innerText || '').trim();
                if (
                  names.some((name) => text.includes(name)) &&
                  /(上传完成|上传中|等待上传|上传失败|重新上传|继续上传|转码中|处理中)/.test(text)
                ) {
                  rows.push(text.slice(0, 600));
                  break;
                }
              }
              if (rows.length >= 8) break;
            }
            return rows;
            """,
            [basename, stem],
        )

    def _prepare_upload_file(self, path_mp4):
        upload_dir = os.path.join(tempfile.gettempdir(), "autopub_bilibili_uploads")
        os.makedirs(upload_dir, exist_ok=True)
        alias_path = os.path.join(upload_dir, f"bilibili_upload_{int(time.time())}.mp4")
        shutil.copy2(path_mp4, alias_path)
        print(f"Prepared short Bilibili upload path: {alias_path}")
        return alias_path

    def _preupload_block_message(self, upload_mp4):
        try:
            size = os.path.getsize(upload_mp4)
            name = quote(os.path.basename(upload_mp4))
            url = (
                "https://member.bilibili.com/preupload"
                f"?r=upos&profile=ugcfx%2Fbup&ssl=0&version=2.14.0.0"
                f"&build=2140000&webVersion=2.14.0&probe_version=20250923"
                f"&upcdn=txa&zone=cs&name={name}&size={size}"
            )
            result = self.driver.execute_async_script(
                """
                const url = arguments[0];
                const cb = arguments[arguments.length - 1];
                fetch(url, {credentials: 'include'})
                  .then(async (response) => cb({
                    status: response.status,
                    text: (await response.text()).slice(0, 1000),
                  }))
                  .catch((error) => cb({error: String(error)}));
                """,
                url,
            )
            text = str(result)
            if result and result.get("status") == 406 and ("上传视频过快" in text or '"code":601' in text):
                return "Bilibili upload rate limit: 您上传视频过快，请稍作休息后再继续。"
            if result and result.get("status") not in (200, 204):
                print(f"Bilibili preupload probe returned: {result}")
        except Exception as exc:
            print(f"Bilibili preupload probe failed: {exc}")
        return None

    def download_image(self, url, local_path='./temp/'):
        response = requests.get(url)
        if response.status_code == 200:
            os.makedirs(local_path, exist_ok=True)
            filename = url.split('/')[-1].split('?')[0]
            file_path = os.path.join(local_path, filename)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            return file_path, 0
        else:
            raise Exception(f"Error downloading image: Status code {response.status_code}")


    def capture_and_crop_screenshot(self, outer_element_selector, inner_element_selector, image_element_selector, output_filename):
        try:
            alert = self.driver.switch_to.alert
            alert.dismiss()  # Dismiss any alerts that might be open
            print("Alert dismissed")
        except NoAlertPresentException:
            print("No alert present")

        try:
            outer_element = self.driver.find_element(By.CSS_SELECTOR, outer_element_selector)
            inner_element = self.driver.find_element(By.CSS_SELECTOR, inner_element_selector)
        except Exception as exc:
            print(f"Captcha crop elements not found, saving full screenshot instead: {exc}")
            self.driver.save_screenshot(output_filename)
            return
        # img_selector = self.driver.find_element(By.CSS_SELECTOR, image_element_selector)




        if outer_element and inner_element:
            # Take screenshot of the whole element
            # Generate a unique timestamp for the temp filename
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
            temp_filename = f'/tmp/bilibili_captha_temp_screenshot_{timestamp}.png'
            # temp_filename = '/tmp/temp_screenshot.png'
            outer_element.screenshot(temp_filename)
            # Open the temporary screenshot and crop it
            img = Image.open(temp_filename)
            outer_element_rect = outer_element.rect
            inner_element_rect = inner_element.rect

            # Calculate the height to crop based on the relative top of the inner element
            new_height = img.height - (outer_element_rect['y'] - inner_element_rect['y'])
            
            if new_height > 0:
                img_cropped = img.crop((0, 0, img.width, new_height))
                img_cropped.save(output_filename)
                print(f'Screenshot saved as {output_filename}')
            else:
                print("No valid crop height calculated; screenshot not cropped.")
            
            # os.remove(temp_filename)  # Clean up the temporary file
        else:
            print('Element not found')

    def take_screenshot(self, url, outer_element_selector=".geetest_holder.geetest_silver", inner_element_selector=".geetest_panel", image_element_selector=".geetest_item_img", local_path='./temp_screenshot/'):
        # Extract the filename from the URL
        filename = url.split('/')[-1].split('?')[0] + '_screenshot.png'
        file_path = os.path.join(local_path, filename)
        os.makedirs(local_path, exist_ok=True)

        # Navigate to the URL
        # self.driver.get(url)  # Assume the URL navigates directly to a page where elements are present
        # time.sleep(2)  # Wait for the page to load completely

        try:
            outer_element = self.driver.find_element(By.CSS_SELECTOR, outer_element_selector)
            # inner_element = self.driver.find_element(By.CSS_SELECTOR, inner_element_selector)
            img_selector = self.driver.find_element(By.CSS_SELECTOR, image_element_selector)

            # Get the bounding rectangle and calculate differences
            outer_rect = self.driver.execute_script("return arguments[0].getBoundingClientRect();", outer_element)
            img_rect = self.driver.execute_script("return arguments[0].getBoundingClientRect();", img_selector)

            # Calculate vertical (top) difference
            print("img_rect['top']: ", img_rect['top'], "outer_rect['top']: ", outer_rect['top'])
            vertical_difference = img_rect['top'] - outer_rect['top']
        except:
            vertical_difference = 50

        print(f"Vertical difference between outer element and image: {vertical_difference}")

        try:
            self.capture_and_crop_screenshot(outer_element_selector, inner_element_selector, image_element_selector, file_path)
        except Exception as exc:
            print(f"Captcha screenshot crop failed, saving full screenshot instead: {exc}")
            self.driver.save_screenshot(file_path)

        try:
            self.download_image(url, local_path=local_path)
        except:
            pass

        print(f"Screenshot saved as {file_path}")
        return file_path, vertical_difference

    def _captcha_present(self):
        try:
            return bool(self.driver.execute_script("""
                return !!document.querySelector(
                    '.geetest_panel_box, .geetest_panel, .geetest_box, .geetest_widget'
                );
            """))
        except Exception:
            return False

    def solve_captcha(self, max_retries=5):
        time.sleep(3)

        # Execute JavaScript to check if the CAPTCHA popup is present
        is_captcha_present = self._captcha_present()

        if not is_captcha_present:
            print("No CAPTCHA detected.")
            return False

        missing = [
            key for key in ("TULING_USERNAME", "TULING_PASSWORD", "TULING_ID")
            if not os.environ.get(key)
        ]
        if missing:
            raise RuntimeError(f"Bilibili CAPTCHA detected but missing env vars: {', '.join(missing)}")
        
        retry = 0
        while is_captcha_present and retry < max_retries:
            print("CAPTCHA detected. Solving...")
            # Execute JavaScript to get the CAPTCHA image URL
            captcha_image_url = self.driver.execute_script("""
                let captchaImageElement = document.querySelector('.geetest_item_wrap, .geetest_item_img');
                if (!captchaImageElement) return '';
                let background = captchaImageElement.style.backgroundImage || '';
                if (background.startsWith('url(')) return background.slice(5, -2);
                if (captchaImageElement.src) return captchaImageElement.src;
                return '';
            """)

            if captcha_image_url:
                # img_path = download_image(captcha_image_url)
                img_path, vertical_difference = self.take_screenshot(captcha_image_url)
                result = b64_api(username=os.environ.get('TULING_USERNAME'), password=os.environ.get('TULING_PASSWORD'), img_path=img_path, ID=os.environ.get('TULING_ID'))
                print(result)
                if not isinstance(result, dict) or "data" not in result:
                    raise RuntimeError(f"Unexpected Tuling CAPTCHA response: {result}")

                # Use the result to simulate the clicks on the CAPTCHA image
                for key in [f'顺序{i}' for i in range(1, 10)]:  # Add more keys if there are more click points
                    if key in result['data']:
                        x = result['data'][key]['X坐标值']
                        y = result['data'][key]['Y坐标值'] - vertical_difference
                        # Execute JavaScript to simulate the click
                        self.driver.execute_script(f"""
                            let rect = document.querySelector('.geetest_item_wrap').getBoundingClientRect();
                            let clickX = rect.left + {x};
                            let clickY = rect.top + {y};
                            let clickEvent = new MouseEvent('click', {{
                                view: window,
                                bubbles: true,
                                cancelable: true,
                                clientX: clickX,
                                clientY: clickY
                            }});
                            document.elementFromPoint(clickX, clickY).dispatchEvent(clickEvent);
                        """)
                        time.sleep(1)  # Wait a second between clicks if needed

                # After solving CAPTCHA, click the confirm button
                self.driver.execute_script("""
                    let confirmButton = document.querySelector('.geetest_commit');
                    if (confirmButton) {
                        confirmButton.click();
                    }
                """)
                print("CAPTCHA solved and confirmed.")
            else:
                print("Failed to get CAPTCHA image URL.")
                self.driver.save_screenshot(f"/tmp/bilibili_captcha_missing_{retry}.png")

            

            try:
                time.sleep(3)
                is_captcha_present = self._captcha_present()
            except:
                print("CAPTCHA confirmed. ")
                is_captcha_present = False

            if not is_captcha_present:
                print("CAPTCHA no longer visible.")
                return True

            retry += 1

        raise RuntimeError("Bilibili CAPTCHA was still visible after solver retries.")

    def _click_submit_and_confirm(self, timeout=180):
        start_url = self.driver.current_url
        submit_xpaths = [
            '//*[normalize-space()="立即投稿"]/ancestor::button[1]',
            '//button[.//*[normalize-space()="立即投稿"]]',
            '//button[contains(normalize-space(.),"立即投稿")]',
            '//*[normalize-space()="立即投稿"]',
        ]
        success_xpaths = [
            '//*[contains(text(),"投稿成功")]',
            '//*[contains(text(),"发布成功")]',
            '//*[contains(text(),"稿件投递成功")]',
            '//*[contains(text(),"审核中")]',
            '//*[contains(text(),"稿件管理")]',
        ]
        failure_xpaths = [
            '//*[contains(text(),"投稿失败")]',
            '//*[contains(text(),"发布失败")]',
            '//*[contains(text(),"提交失败")]',
            '//*[contains(text(),"上传失败")]',
        ]

        submit_button, submit_xpath = self._find_visible(submit_xpaths)
        if submit_button is None:
            log_html_snapshot(self.driver, "bilibili", "submit_button_missing")
            raise RuntimeError("Bilibili submit button was not found.")
        if not self._safe_click(submit_button):
            raise RuntimeError(f"Failed to click Bilibili submit button: {submit_xpath}")
        print(f"Clicked Bilibili submit button using selector: {submit_xpath}")

        start_time = time.time()
        while time.time() - start_time <= timeout:
            sms_message = self._sms_verification_text()
            if sms_message:
                self._handle_sms_verification_gate(self.path_mp4)
                time.sleep(5)
                continue

            if self._captcha_present():
                self.solve_captcha(max_retries=5)
                time.sleep(5)

            failure_element, failure_xpath = self._find_visible(failure_xpaths)
            if failure_element is not None:
                text = (failure_element.text or "").strip()
                log_html_snapshot(self.driver, "bilibili", "publish_failed")
                raise RuntimeError(f"Bilibili publish failed: {failure_xpath} text={text!r}")

            success_element, success_xpath = self._find_visible(success_xpaths)
            if success_element is not None:
                print(f"Bilibili publish confirmed via page state: {success_xpath}")
                return True

            current_url = self.driver.current_url
            if current_url != start_url and ("upload-manager" in current_url or "platform" in current_url):
                print(f"Bilibili publish likely completed; URL changed to {current_url}")
                return True

            submit_button, _ = self._find_visible(submit_xpaths)
            if submit_button is None and current_url != start_url:
                print(f"Bilibili submit button disappeared after URL changed to {current_url}.")
                return True

            print(f"Waiting for Bilibili publish confirmation... Current URL: {current_url}")
            time.sleep(5)

        log_html_snapshot(self.driver, "bilibili", "publish_timeout")
        raise RuntimeError("Timed out waiting for Bilibili publish confirmation.")

    def click_specific_tag_if_exists(self, tag_text):
        try:
            # Construct XPath to find the tag based on its visible text
            tag_xpath = f"//span[contains(text(), '{tag_text}')]"
            # Wait until the tag is clickable and then click on it
            tag_element = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, tag_xpath)))
            tag_element.click()
            print(f"Clicked on the tag: {tag_text}")
            return True
        except TimeoutException:
            print(f"Tag '{tag_text}' not found or not clickable.")
            return False

    def search_and_select_topic(self, topic_name):
        try:
            print(f"Attempting to open the search dialog to search for '{topic_name}'.")
            search_dialog_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '搜索更多话题')]")))
            self.driver.execute_script("arguments[0].click();", search_dialog_button)
            print("Search dialog opened via JavaScript click.")

            time.sleep(2)  # Ensure UI has time to respond

            search_input = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "input.bcc-search-input")))
            search_input.clear()
            print("Input cleared.")
            search_input.send_keys(topic_name)
            print(f"Entered '{topic_name}' in the search box.")
            search_input.send_keys(Keys.ENTER)
            print("Search executed.")

            time.sleep(2)  # Wait for search results

            topic_xpath = f"//div[contains(@class, 'topic-tag-name') and contains(text(), '{topic_name}')]"
            topic_element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, topic_xpath)))
            self.driver.execute_script("arguments[0].click();", topic_element)
            print(f"Topic '{topic_name}' selected via JavaScript click.")

            time.sleep(2)  # Wait for the selection to process

            confirm_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[.//span[contains(text(), '确定')]]")))
            self.driver.execute_script("arguments[0].click();", confirm_button)
            print("Confirmation button clicked via JavaScript and topic added.")
            return True

        except Exception as e:
            print(f"Topic failed in selection: ", str(e))
            return False

    def publish(self):
        if self.retry_count < 3:  # maximum 3 tries (initial + 2 retries)
            try:
                driver = self.driver
                path_mp4 = self.path_mp4
                path_cover = self.path_cover
                metadata = self.metadata
                test = self.test

                print("Starting the publishing process on Bilibili...")
                self._reset_upload_page()
                time.sleep(1)
                dismiss_alert(driver) # assumed to be handled externally
                time.sleep(10)

                bring_to_front(["哔哩哔哩"])
                close_extra_tabs(driver)
                
                upload_mp4 = self._prepare_upload_file(path_mp4)
                print(f"Uploading video from path: {upload_mp4}")
                upload_input_xpath = '//input[@type="file" and contains(@accept,"mp4")]'
                time.sleep(3)        
                bring_to_front(["哔哩哔哩"])
                driver.find_element(By.XPATH, upload_input_xpath).send_keys(upload_mp4)

                print("Waiting for the video to be uploaded...")
                time.sleep(3)
                # upload_status_xpath = '//*[contains(text(),"上传完成")]'
                # failure_xpath = '//*[contains(text(),"上传失败")]'
                upload_status_xpath = (
                    '//*[normalize-space()="上传完成" or contains(normalize-space(),"上传完成")]'
                )
                # WebDriverWait(driver, 3600).until(EC.presence_of_element_located((By.XPATH, '//*[text()="上传完成"]')))
                start_time = time.time()
                timeout = 3600  # 3600 seconds timeout
                failed_seen = 0


                while True:
                    if time.time() - start_time > timeout:
                        raise Exception("Timeout reached while waiting for video to be uploaded or for a failure message.")

                    self._close_optional_upload_overlays()
                    if self._resume_upload_if_paused():
                        failed_seen = 0
                        time.sleep(5)
                        continue

                    status_rows = self._current_upload_status_text(upload_mp4)
                    if status_rows:
                        print("Bilibili current upload status:", " | ".join(status_rows[:2]))
                    sms_message = self._sms_verification_text()
                    if sms_message:
                        self._handle_sms_verification_gate(upload_mp4)
                        failed_seen = 0
                        time.sleep(5)
                        continue
                    if any("0.0MB/0.0MB" in row and "0%" in row for row in status_rows):
                        block_message = self._preupload_block_message(upload_mp4)
                        if block_message:
                            raise BilibiliRateLimitException(block_message)
                    if any(("上传完成" in row or "重新上传" in row) for row in status_rows):
                        print("Video uploaded successfully!")
                        break

                    if any("上传失败" in row for row in status_rows) or self._upload_failure_visible():
                        failed_seen += 1
                        print(f"Bilibili upload failure indicator visible ({failed_seen}/3).")
                        if failed_seen >= 3:
                            raise Exception("Video upload failed.")
                    else:
                        failed_seen = 0

                    # Backward compatibility if Bilibili changes the row markup,
                    # but only after the file-specific probe had no status rows.
                    if not status_rows:
                        try:
                            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, upload_status_xpath)))
                            print("Generic Bilibili upload completion prompt detected.")
                            break
                        except TimeoutException:
                            pass

                    time.sleep(5)  # Wait a bit before checking again


                print("Handling cover upload.")
                try:
                    resized_cover = crop_and_resize_cover_image(path_cover)
                    if not resized_cover:
                        raise RuntimeError("Bilibili cover resize failed.")
                    # Click on the '更改封面' button to start the cover upload process
                    edit_cover_button_xpath = '//*[text()="更改封面"]'
                    time.sleep(3)
                    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, edit_cover_button_xpath))).click()
                    # Wait for the '上传封面' option to become clickable and click it
                    upload_cover_option_xpath = '//*[text()="上传封面"]'
                    time.sleep(3)
                    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, upload_cover_option_xpath))).click()
                    file_input_xpath = "//input[@type='file' and @accept='image/png, image/jpeg']"
                    time.sleep(3)
                    file_input_element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, file_input_xpath)))
                    # Send the file path to the hidden file input element
                    time.sleep(3)
                    file_input_element.send_keys(resized_cover)
                    # Define the JavaScript code
                    js_code = """
                    var finishButton = [...document.querySelectorAll('.bcc-button--primary')].find(el => el.innerText.includes('完成'));
                    if (finishButton) {
                        finishButton.click();
                        return "Clicked '完成' button.";
                    } else {
                        return "'完成' button not found.";
                    }
                    """
                    # Execute the JavaScript code
                    time.sleep(3)
                    result = driver.execute_script(js_code)
                    # Print the result of the JavaScript execution
                    print(result)
                    print("Cover upload finished.")
                except Exception as exc:
                    print(f"Cover upload skipped; using Bilibili default cover: {exc}")

                # Enter Title
                print("Entering title...")
                title_input_xpath = '//input[contains(@placeholder,"请输入稿件标题")]'
                time.sleep(3)        
                # wait_for_element_to_be_clickable(title_input_xpath)
                driver.find_element(By.XPATH, title_input_xpath).clear()
                time.sleep(3)        
                driver.find_element(By.XPATH, title_input_xpath).send_keys(metadata['title'][:30])

                # Enter Description
                print("Entering description...")
                description_with_tags = metadata['long_description'] + " " + " ".join([f"#{tag}" for tag in metadata['tags']])
                desc_input_xpath = '//*[@editor_id="desc_at_editor"]//br'
                time.sleep(3)
                # wait_for_element_to_be_clickable(desc_input_xpath)
                driver.find_element(By.XPATH, desc_input_xpath).send_keys(description_with_tags[:250])

                # Select Category
                print("Selecting category...")
                category_select_xpath = '//*[contains(@class,"select-item-cont")]'
                # wait_for_element_to_be_clickable(category_select_xpath)
                driver.find_element(By.XPATH, category_select_xpath).click()
                time.sleep(1)
                driver.find_element(By.XPATH, '//*[text()="推荐选择"]').click()
                time.sleep(1)
                driver.find_element(By.XPATH, '//*[text()="日常"]').click()
                # time.sleep(1)


                # Click on the specific tag before adding other tags
                success = self.click_specific_tag_if_exists("随手记录我的生活碎片")
                if not success:
                    self.search_and_select_topic("随手记录我的生活碎片")


                # Add Tags
                print("Adding tags...")
                tag_input_xpath = '//input[@placeholder="按回车键Enter创建标签"]'
                for tag in metadata['tags'][:-1]:
                    # wait_for_element_to_be_clickable(tag_input_xpath)
                    time.sleep(1)
                    driver.find_element(By.XPATH, tag_input_xpath).send_keys(tag)
                    time.sleep(1)
                    driver.find_element(By.XPATH, tag_input_xpath).send_keys(Keys.ENTER)

                # Prompt for Publishing
                if test:
                    user_input = input("Do you want to publish now? Type 'yes' to confirm: ").strip().lower()
                else:
                    user_input = "yes"
                if user_input == 'yes':
                    print("Publishing the video...")
                    time.sleep(3)
                    self._click_submit_and_confirm(timeout=240)
                    print("Video published successfully!")
                else:
                    print("Publishing cancelled by the user.")
                
                self.retry_count = 0  # reset retry count after successful execution
                return True
            except Exception as e:
                print(f"An error occurred: {e}")
                traceback.print_exc()
                if isinstance(e, (BilibiliRateLimitException, BilibiliSmsVerificationRequired)):
                    raise
                self.retry_count += 1
                print(f"Retrying the whole process... Attempt {self.retry_count}")
                return self.publish()  # Retry the whole process
        else:
            raise RuntimeError("Maximum retry attempts reached. Bilibili process failed.")

def get_media_paths(catalog):
    path = pathlib.Path(catalog)
    path_mp4 = next((str(p) for p in path.glob('*.mp4')), None)
    path_cover = next((str(p) for p in path.glob('*') if p.suffix in ['.png', '.jpg']), None)
    return path_mp4, path_cover

if __name__ == "__main__":
    # Constants
    catalog_mp4 = r"/Users/lachlan/Documents/iProjects/auto-publish/videos"
    chrome_driver_path = "/user/local/bin/chromedriver"  # Change this to your Chromedriver path

    # Chrome options
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:5003")

    # Initialize the driver
    driver = webdriver.Chrome(options=options)

    # Get the video and cover paths
    path_mp4, path_cover = get_media_paths(catalog_mp4)
    if not path_mp4 or not path_cover:
        print("Video or cover file not found. Exiting...")
    else:
        print(f"Found video path: {path_mp4}")
        print(f"Found cover path: {path_cover}")

        # Metadata for the post
        metadata = {
            "title": "品味经典美味：超赞的烤鸡",
            "brief_description": "跟随我们的味蕾之旅，发现为何这款烤鸡让人赞不绝口！",
            "tags": ["美食", "烤鸡", "推荐"]
        }

        # Create an instance of the BilibiliPublisher
        pub_bilibililisher = BilibiliPublisher(
            driver=driver,
            path_mp4=path_mp4,
            path_cover=path_cover,
            metadata=metadata
        )

        # Start publishing process
        pub_bilibililisher.publish()
