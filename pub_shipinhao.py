import time
import json
import traceback
import os
from selenium import webdriver
from selenium.common.exceptions import (
    NoAlertPresentException,
    NoSuchElementException,
    NoSuchFrameException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import dismiss_alert, bring_to_front, close_extra_tabs, log_html_snapshot
from login_shipinhao import ShiPinHaoLogin
import traceback

import re

SHIPINHAO_CREATE_URL = "https://channels.weixin.qq.com/platform/post/create"
SHIPINHAO_WINDOW_PATTERNS = ["视频号", "视频号助手", "发表动态", "视频管理"]
SHIPINHAO_READY_SELECTORS = [
    ".post-create-wrap",
    ".post-edit-wrap",
    ".post-upload-wrap",
    ".input-editor[contenteditable]",
    'input[type="file"][accept*="video"]',
]
SHIPINHAO_UPLOAD_INPUT_SELECTORS = [
    'input[type="file"][accept*="video"]',
    '.post-upload-wrap input[type="file"]',
    'input[type="file"]',
]
DEEP_QUERY_SCRIPT = r"""
const selector = arguments[0];
const requireVisible = !!arguments[1];
const exactText = arguments.length > 2 ? arguments[2] : null;
const maxDepth = 8;

function isVisible(el) {
  if (!el) return false;
  const style = window.getComputedStyle(el);
  if (!style) return false;
  if (style.display === 'none' || style.visibility === 'hidden' || style.visibility === 'collapse') {
    return false;
  }
  if (parseFloat(style.opacity || '1') === 0) {
    return false;
  }
  const rect = el.getBoundingClientRect();
  return !!(rect.width || rect.height || el.getClientRects().length);
}

function matchesText(el, text) {
  if (text === null || text === undefined) return true;
  const value = (el.textContent || '').replace(/\s+/g, ' ').trim();
  if (!value) return false;
  if (arguments[2]) {
    return value === text;
  }
  return value.includes(text);
}

function queryAllDeep(root, depth, acc) {
  if (!root || depth > maxDepth || !root.querySelectorAll) return acc;
  for (const el of root.querySelectorAll(selector)) {
    acc.push(el);
  }
  for (const el of root.querySelectorAll('*')) {
    if (el.shadowRoot) {
      queryAllDeep(el.shadowRoot, depth + 1, acc);
    }
  }
  return acc;
}

const matches = queryAllDeep(document, 0, []);
for (const el of matches) {
  if ((!requireVisible || isVisible(el)) && matchesText(el, exactText, !!arguments[3])) {
    return el;
  }
}
return null;
"""

DEEP_EXISTS_SCRIPT = r"""
const selector = arguments[0];
const requireVisible = !!arguments[1];
const exactText = arguments.length > 2 ? arguments[2] : null;
const exactMatch = !!arguments[3];
const maxDepth = 8;

function isVisible(el) {
  if (!el) return false;
  const style = window.getComputedStyle(el);
  if (!style) return false;
  if (style.display === 'none' || style.visibility === 'hidden' || style.visibility === 'collapse') {
    return false;
  }
  if (parseFloat(style.opacity || '1') === 0) {
    return false;
  }
  const rect = el.getBoundingClientRect();
  return !!(rect.width || rect.height || el.getClientRects().length);
}

function matchesText(el, text, exact) {
  if (text === null || text === undefined) return true;
  const value = (el.textContent || '').replace(/\s+/g, ' ').trim();
  if (!value) return false;
  return exact ? value === text : value.includes(text);
}

function queryAllDeep(root, depth, acc) {
  if (!root || depth > maxDepth || !root.querySelectorAll) return acc;
  for (const el of root.querySelectorAll(selector)) {
    acc.push(el);
  }
  for (const el of root.querySelectorAll('*')) {
    if (el.shadowRoot) {
      queryAllDeep(el.shadowRoot, depth + 1, acc);
    }
  }
  return acc;
}

const matches = queryAllDeep(document, 0, []);
for (const el of matches) {
  if ((!requireVisible || isVisible(el)) && matchesText(el, exactText, exactMatch)) {
    return true;
  }
}
return false;
"""

# def dismiss_alert(driver):
#     try:
#         alert = driver.switch_to.alert
#         alert.accept()
#         print("Alert was present and accepted.")
#     except NoAlertPresentException:
#         print("No alert present.")

UPLOAD_COMPLETE_XPATHS = [
    '//*[contains(text(), "删除")]',
    '//*[contains(text(), "重新上传")]',
    '//*[contains(text(), "替换")]',
    '//*[contains(text(), "上传成功")]',
    '//*[contains(text(), "上传完成")]',
    '//*[contains(text(), "转码中")]',
    '//div[contains(@class, "ant-upload-list-item") and (contains(@class, "done") or contains(@class, "success"))]',
    '//div[contains(@class, "ant-upload-list-item")]',
    '//div[contains(@class, "post-upload-wrap")]//video',
]

def is_upload_complete_indicator_present(driver):
    if _content_frame_upload_ready(driver):
        print("Upload preview is ready in content frame, upload likely complete.")
        return True
    for xpath in UPLOAD_COMPLETE_XPATHS:
        if _indicator_present_in_content_frame(driver, xpath):
            print(f"Upload indicator found in content frame ({xpath}), upload likely complete.")
            return True
        try:
            element = driver.find_element(By.XPATH, xpath)
            if element and element.is_displayed():
                print(f"Upload indicator found ({xpath}), upload likely complete.")
                return True
        except NoSuchElementException:
            continue
    return False


def _content_frame_upload_ready(driver):
    expression = r"""
(() => {
  const frame = document.querySelector("iframe[name=content]");
  if (!frame || !frame.contentDocument) return false;
  const wrap = frame.contentDocument.querySelector(".post-upload-wrap");
  if (!wrap) return false;
  const previewVideo = wrap.querySelector('video[src^="blob:"]');
  const uploading = wrap.querySelector(".ant-upload.ant-upload-drag-uploading");
  return !!previewVideo && !uploading;
})()
"""
    try:
        result = driver.execute_cdp_cmd(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True},
        )
    except Exception:
        return False

    payload = result.get("result") or {}
    return bool(payload.get("value"))


def _indicator_present_in_content_frame(driver, xpath):
    if not _switch_to_content_frame(driver):
        return False

    try:
        elements = driver.find_elements(By.XPATH, xpath)
        for element in elements:
            try:
                if element and element.is_displayed():
                    return True
            except StaleElementReferenceException:
                continue
    except Exception:
        return False
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass

    return False

def wait_for_element(driver, xpath, duration=30):
    return WebDriverWait(driver, duration).until(EC.presence_of_element_located((By.XPATH, xpath)))

def wait_for_element_clickable(driver, xpath, duration=30):
    return WebDriverWait(driver, duration).until(EC.element_to_be_clickable((By.XPATH, xpath)))

def wait_for_element_visible(driver, xpath, duration=30):
    return WebDriverWait(driver, duration).until(EC.visibility_of_element_located((By.XPATH, xpath)))


def wait_for_any_element(driver, xpaths, duration=30):
    def _locate(current_driver):
        for xpath in xpaths:
            try:
                element = current_driver.find_element(By.XPATH, xpath)
                if element:
                    return element
            except NoSuchElementException:
                continue
        return False

    return WebDriverWait(driver, duration).until(_locate)


def find_deep_css(driver, selector, duration=30, visible=True):
    return WebDriverWait(driver, duration).until(
        lambda current_driver: _run_deep_query(current_driver, selector, visible)
    )


def find_deep_text(driver, selector, text, duration=30, visible=True, exact=False):
    return WebDriverWait(driver, duration).until(
        lambda current_driver: _run_deep_query(current_driver, selector, visible, text, exact)
    )


def _run_deep_query(driver, selector, visible=True, text=None, exact=False):
    frame_match = _find_in_content_frame(driver, selector, visible, text, exact)
    if frame_match:
        return frame_match
    try:
        if text is None:
            return driver.execute_script(DEEP_QUERY_SCRIPT, selector, visible)
        return driver.execute_script(DEEP_QUERY_SCRIPT, selector, visible, text, exact)
    except StaleElementReferenceException:
        return False


def deep_exists(driver, selector, visible=True, text=None, exact=False):
    frame_match = _find_in_content_frame(driver, selector, visible, text, exact)
    if frame_match:
        return True
    try:
        if text is None:
            return bool(driver.execute_script(DEEP_EXISTS_SCRIPT, selector, visible))
        return bool(driver.execute_script(DEEP_EXISTS_SCRIPT, selector, visible, text, exact))
    except StaleElementReferenceException:
        return False


def _switch_to_content_frame(driver):
    try:
        driver.switch_to.default_content()
    except Exception:
        return False
    try:
        driver.switch_to.frame("content")
        return True
    except (NoSuchFrameException, NoSuchElementException, StaleElementReferenceException):
        try:
            frame = driver.find_element(By.CSS_SELECTOR, 'iframe[name="content"]')
            driver.switch_to.frame(frame)
            return True
        except Exception:
            try:
                driver.switch_to.default_content()
            except Exception:
                pass
            return False


def _matches_element_text(element, text, exact=False):
    if text is None:
        return True
    value = (element.text or "").strip()
    if not value:
        return False
    if exact:
        return value == text
    return text in value


def _find_in_content_frame(driver, selector, visible=True, text=None, exact=False):
    if not _switch_to_content_frame(driver):
        return False

    try:
        candidates = driver.find_elements(By.CSS_SELECTOR, selector)
    except Exception:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass
        return False

    for candidate in candidates:
        try:
            if visible and not candidate.is_displayed():
                continue
            if not _matches_element_text(candidate, text, exact):
                continue
            return candidate
        except StaleElementReferenceException:
            continue

    try:
        driver.switch_to.default_content()
    except Exception:
        pass
    return False


def find_any_in_content_frame(driver, selectors, duration=30, visible=True):
    def _locate(current_driver):
        if not _switch_to_content_frame(current_driver):
            return False

        for selector in selectors:
            try:
                candidates = current_driver.find_elements(By.CSS_SELECTOR, selector)
            except Exception:
                continue

            for candidate in candidates:
                try:
                    if visible and not candidate.is_displayed():
                        continue
                    return candidate
                except StaleElementReferenceException:
                    continue
        return False

    return WebDriverWait(driver, duration).until(_locate)


def send_file_to_content_frame(driver, selectors, file_path, duration=30):
    deadline = time.time() + duration
    last_error = None

    while time.time() < deadline:
        for selector in selectors:
            object_id = _resolve_content_frame_input_object_id(driver, selector)
            if object_id:
                try:
                    driver.execute_cdp_cmd(
                        "DOM.setFileInputFiles",
                        {"files": [file_path], "objectId": object_id},
                    )
                    return True
                except Exception as exc:
                    last_error = exc

            if not _switch_to_content_frame(driver):
                continue

            try:
                candidates = driver.find_elements(By.CSS_SELECTOR, selector)
            except Exception as exc:
                last_error = exc
                continue

            for candidate in candidates:
                try:
                    candidate.send_keys(file_path)
                    return True
                except StaleElementReferenceException as exc:
                    last_error = exc
                    continue
                except Exception as exc:
                    last_error = exc
                    continue

        time.sleep(0.5)

    if last_error:
        raise last_error
    raise TimeoutException("Timed out sending file to Shipinhao upload input.")


def _resolve_content_frame_input_object_id(driver, selector):
    expression = f"""
(() => {{
  const frame = document.querySelector("iframe[name=content]");
  if (!frame || !frame.contentDocument) return null;
  return frame.contentDocument.querySelector({json.dumps(selector)});
}})()
"""
    try:
        result = driver.execute_cdp_cmd(
            "Runtime.evaluate",
            {
                "expression": expression,
                "objectGroup": "autopub",
                "includeCommandLineAPI": True,
            },
        )
    except Exception:
        return None

    payload = result.get("result") or {}
    return payload.get("objectId")

def safe_click(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    try:
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)

def dismiss_overlays(driver):
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    except Exception:
        pass
    try:
        driver.execute_script(
            "document.querySelectorAll('.feed-cover').forEach(el => el.style.pointerEvents='none');"
        )
    except Exception:
        pass


def save_debug_snapshot(driver, label):
    log_html_snapshot(driver, "shipinhao", label)
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    screenshot_path = os.path.join(logs_dir, f"shipinhao-{label}.png")
    try:
        driver.save_screenshot(screenshot_path)
        print(f"Saved Shipinhao screenshot to {screenshot_path}")
    except Exception as exc:
        print(f"Failed to save Shipinhao screenshot for {label}: {exc}")


def wait_for_publish_page_ready(driver, duration=45):
    try:
        driver.switch_to.default_content()
    except Exception:
        pass

    dismiss_alert(driver)
    dismiss_overlays(driver)

    try:
        WebDriverWait(driver, duration).until(
            lambda current_driver: any(
                deep_exists(current_driver, selector, visible=True)
                for selector in SHIPINHAO_READY_SELECTORS
            )
        )
        print(f"Shipinhao editor is ready at {driver.current_url}")
        return True
    except TimeoutException:
        print(f"Timed out waiting for Shipinhao editor. title={driver.title!r} url={driver.current_url!r}")
        save_debug_snapshot(driver, "publish_ready_timeout")
        raise

class ShiPinHaoPublisher:
    def __init__(self, driver, video_path, thumbnail_path, metadata, test=False):
        self.driver = driver
        self.video_path = video_path
        self.thumbnail_path = thumbnail_path
        self.metadata = metadata
        self.test = test
        self.retry_count = 0  # initialize retry count

        shi_pin_hao_login = ShiPinHaoLogin(driver)
        shi_pin_hao_login.check_and_act()


    def clear_and_type(self, element, text):
        tag_name = (element.tag_name or "").lower()
        contenteditable = (element.get_attribute("contenteditable") or "").lower() == "true"
        safe_click(self.driver, element)
        time.sleep(0.5)
        if tag_name in {"input", "textarea"}:
            element.clear()
        elif contenteditable:
            element.send_keys(Keys.CONTROL, "a")
            element.send_keys(Keys.BACKSPACE)
        else:
            self.driver.execute_script("arguments[0].value = '';", element)
        time.sleep(0.5)
        element.send_keys(text)

    def upload_and_confirm_cover(self):
        try:
            # Wait and click on '更换封面' if it exists
            change_cover_button = find_deep_text(self.driver, "button, span, div", "更换封面", duration=10)
            safe_click(self.driver, change_cover_button)
            time.sleep(2)

            # Click on '上传封面' to start the cover upload
            upload_cover_button = find_deep_text(self.driver, "button, span, div", "上传封面", duration=10)
            safe_click(self.driver, upload_cover_button)
            time.sleep(2)

            # Interact with the file input to upload the cover file
            file_input = find_deep_css(self.driver, 'input[type="file"][accept*="image"]', duration=10, visible=False)
            file_input.send_keys(self.thumbnail_path)
            time.sleep(2)

            # Confirm the upload by clicking on '确认'
            confirm_button = find_deep_text(self.driver, "button, span, div", "确认", duration=10)
            safe_click(self.driver, confirm_button)
            time.sleep(2)

        except Exception as e:
            print(f"An error occurred during cover upload: {e}")
            # Close the dialog if there's an error
            try:
                close_button = find_deep_css(self.driver, "button.weui-desktop-dialog__close-btn", duration=10)
                safe_click(self.driver, close_button)
                time.sleep(2)
                print("Closed the cover upload dialog due to an error.")
            except Exception as e:
                print(f"An error occurred while trying to close the dialog: {e}")

    def clean_title(self, title):
        # Allowed special characters: 书名号(「」), 引号("“”"), 冒号(:), 加号(+), 问号(?), 百分号(%), 摄氏度(°)
        # Replace comma with space
        title = title.replace(',', ' ')
        
        # Remove characters not in the allowed list using regular expression
        allowed_chars_regex = r'[a-zA-Z0-9\u4e00-\u9fff「」"“”:\+\?%° ]'  # Add space at the end to allow spaces
        clean_title = ''.join(re.findall(allowed_chars_regex, title))
        
        return clean_title

    # def set_location(self, driver):
    #     try:
    #         # Click on the position display wrapper
    #         position_display_wrap = wait_for_element(driver, '//*[@class="position-display-wrap"]', 30)
    #         position_display_wrap.click()
    #         time.sleep(3)

    #         # Enter location in the search box
    #         location_input = wait_for_element(driver, '//input[@placeholder="搜索附近位置"]', 30)
    #         self.clear_and_type(location_input, "香港特别行政区香港大学")
    #         time.sleep(3)

    #         # Click the search button
    #         search_button = wait_for_element(driver, '//button[contains(@class, "weui-desktop-icon-btn weui-desktop-search__btn")]', 30)
    #         search_button.click()
    #         time.sleep(3)

    #         # Try clicking on "香港大学" if available
    #         hku_option = wait_for_element_clickable(driver, "//div[contains(@class, 'location-item-info')]//div[text()='香港大学']", 30)
    #         hku_option.click()
    #     except:
    #         # If "香港大学" not found, click "不显示位置"
    #         no_location_option = wait_for_element_clickable(driver, "//div[contains(@class, 'location-item-info')]//div[text()='不显示位置']", 30)
    #         no_location_option.click()
    #     finally:
    #         time.sleep(3)

    def set_location(self, driver):
        location_options = [
            ("香港特别行政区香港大学", "香港大学"),
            ("香港特别行政区", "香港特别行政区"),
            (None, "不显示位置")  # Use None to indicate no typing is required
        ]
        
        for location_input_text, _ in location_options:
            try:
                dismiss_overlays(driver)
                # Click on the position display wrapper
                position_display_wrap = find_deep_css(driver, ".position-display-wrap", 30)
                safe_click(driver, position_display_wrap)
                time.sleep(3)

                if location_input_text:
                    # Enter location in the search box
                    location_input = find_deep_css(driver, 'input[placeholder="搜索附近位置"]', 30)
                    self.clear_and_type(location_input, location_input_text)
                    time.sleep(3)

                    # Click the search button if needed
                    search_button = find_deep_css(driver, "button.weui-desktop-search__btn", 30)
                    safe_click(driver, search_button)
                    time.sleep(3)

                click_successful = False
                for _, location_click_text in location_options:
                    try:
                        # Try clicking on the specified location
                        location_option = find_deep_text(
                            driver,
                            ".location-item-info .name",
                            location_click_text,
                            30,
                            exact=True,
                        )
                        safe_click(driver, location_option)
                        time.sleep(3)
                        print(f"Clicked on location: {location_click_text}")
                        click_successful = True
                        break  # Break the loop if click was successful
                    except Exception as e:
                        print(f"Could not click on location: {location_click_text}. Error: {e}")
                
                if click_successful:
                    break

            except Exception as e:
                print(f"Could not click with input: {location_input_text}. Error: {e}")
                if location_input_text is None:
                    print("Failed to set any location. Please check the availability of the location options.")
                    break  # Exit loop if "不显示位置" also fails

    
    def publish(self):
        if self.retry_count < 3:  # maximum 3 tries (initial + 2 retries)
            try:
                driver = self.driver
                video_path = self.video_path
                thumbnail_path = self.thumbnail_path
                metadata = self.metadata
                test = self.test

                print("Starting the publishing process on ShiPinHao...")
                driver.get(SHIPINHAO_CREATE_URL)
                dismiss_alert(driver)
                time.sleep(3)

                bring_to_front(SHIPINHAO_WINDOW_PATTERNS)
                close_extra_tabs(driver)

                wait_for_publish_page_ready(driver, 45)
                dismiss_alert(driver)
                time.sleep(2)

                # Upload video
                bring_to_front(SHIPINHAO_WINDOW_PATTERNS)
                find_any_in_content_frame(
                    driver,
                    SHIPINHAO_UPLOAD_INPUT_SELECTORS,
                    duration=30,
                    visible=False,
                )
                send_file_to_content_frame(
                    driver,
                    SHIPINHAO_UPLOAD_INPUT_SELECTORS,
                    video_path,
                    duration=30,
                )
                print("Video uploading...")

                start_time = time.time()
                timeout = 3600  # 3600 seconds timeout
                while not is_upload_complete_indicator_present(driver):
                    if time.time() - start_time > timeout:
                        raise Exception("Timeout reached while waiting for video to be uploaded.")
                    print("Waiting for the video to upload or for completion indicators to appear...")
                    dismiss_alert(driver)
                    time.sleep(5)

                time.sleep(10)  # Wait for 10 seconds after detecting the delete button
                print("Video uploaded or completion indicator detected!")

                # Upload and confirm cover
                self.upload_and_confirm_cover()
                time.sleep(3)

                # Set description
                video_description_with_tags = self.metadata["long_description"] + " " + " ".join("#" + tag for tag in self.metadata["tags"])
                description_input = find_deep_css(driver, '.input-editor[contenteditable]', 30)
                self.clear_and_type(description_input, video_description_with_tags)
                time.sleep(3)

                # # Set location
                # position_display_wrap = wait_for_element(driver, '//*[@class="position-display-wrap"]', 30)
                # position_display_wrap.click()
                # time.sleep(3)

                # location_input = wait_for_element(driver, '//input[@placeholder="搜索附近位置"]', 30)
                # self.clear_and_type(location_input, "香港特别行政区香港大学")
                # time.sleep(3)

                # search_button = wait_for_element(driver, '//button[contains(@class, "weui-desktop-icon-btn weui-desktop-search__btn")]', 30)
                # search_button.click()
                # time.sleep(3)

                # hku_option = wait_for_element_clickable(driver, "//div[contains(@class, 'location-item-info')]//div[text()='香港大学']", 30)
                # hku_option.click()
                # time.sleep(3)

                if os.environ.get("AUTOPUB_SHIPINHAO_LOCATION", "0") == "1":
                    self.set_location(driver)
                else:
                    print("Skipping location selection for ShiPinHao.")

                # Set playlist
                collection_dropdown = find_deep_css(
                    driver,
                    ".post-album-display-wrap .display-text",
                    30,
                )
                safe_click(driver, collection_dropdown)
                time.sleep(3)

                try:
                    simple_life_collection = find_deep_text(
                        driver,
                        ".common-option-list-wrap.option-list-wrap .name",
                        "简单生活",
                        30,
                        exact=True,
                    )
                    safe_click(driver, simple_life_collection)
                    time.sleep(3)
                except Exception as e:
                    print(f"Collection '简单生活' not found or not clickable: {e}")

                # Set short title
                title = metadata['title'] if 6 <= len(metadata['title']) <= 16 else metadata['brief_description'][:16]
                short_title_input = find_deep_css(driver, 'input[placeholder*="概括视频主要内容"]', 30)
                self.clear_and_type(short_title_input, self.clean_title(title[:16]))
                time.sleep(3)

#                 # Original declaration
#                 original_content_checkbox = driver.find_element(By.XPATH, '//input[@class="ant-checkbox-input" and @type="checkbox"]')
#                 original_content_checkbox.click()
#                 time.sleep(3)

#                 # Define the dropdown and select "生活"
#                 dropdown_label = driver.find_element(By.XPATH, '//div[@class="weui-desktop-form__dropdown weui-desktop-form__dropdown__default"]/dl')
#                 dropdown_label.click()
#                 time.sleep(3)

#                 life_option = driver.find_element(By.XPATH, '//span[@class="weui-desktop-dropdown__list-ele__text" and text()="生活"]')
#                 life_option.click()
#                 time.sleep(3)

#                 # Check the agreement checkbox
#                 agreement_checkbox = driver.find_element(By.XPATH, '//div[@class="original-proto-wrapper"]//input[@type="checkbox"]')
#                 if not agreement_checkbox.is_selected():
#                     agreement_checkbox.click()
#                     time.sleep(3)

#                 # Click on the "声明原创" button once it's clickable
#                 declare_original_button = wait_for_element_clickable(driver, '//div[@class="weui-desktop-dialog__ft"]//button[contains(text(), "声明原创")]', 30)
#                 declare_original_button.click()
#                 time.sleep(3)

                # ------------------ Step 6: Declare original content ------------------
                print("Declaring original content...")
                declare_original_checkbox = find_deep_css(driver, ".declare-original-checkbox input.ant-checkbox-input", 10)
                safe_click(driver, declare_original_checkbox)
                time.sleep(2)

                dialog_checkbox = find_deep_css(driver, ".original-proto-wrapper input.ant-checkbox-input", 10)
                safe_click(driver, dialog_checkbox)
                time.sleep(1)

                declare_button = find_deep_text(driver, "button", "声明原创", 10, exact=True)
                safe_click(driver, declare_button)
                time.sleep(3)

                # Click publish button
                if test:
                    user_input = input("Do you want to publish now? Type 'yes' to confirm: ").strip().lower()
                else:
                    user_input = "yes"
                if user_input == 'yes':
                    submit_button = find_deep_text(driver, "button", "发表", 30, exact=True)
                    safe_click(driver, submit_button)
                    time.sleep(10)
                    print("Publishing...")
                else:
                    print("Publishing cancelled by user.")

                print("Process completed successfully!")
                self.retry_count = 0  # reset retry count after successful execution
                return True
            except Exception as e:
                print(f"An error occurred: {e}")
                traceback.print_exc()
                save_debug_snapshot(driver, f"publish_attempt_{self.retry_count + 1}")
                self.retry_count += 1
                if self.retry_count >= 3:
                    message = "Maximum retry attempts reached. Process failed."
                    print(message)
                    raise RuntimeError(message) from e
                print(f"Retrying the whole process... Attempt {self.retry_count}")
                return self.publish()  # Retry the whole process
        else:
            message = "Maximum retry attempts reached. Process failed."
            print(message)
            raise RuntimeError(message)


if __name__ == "__main__":
    video_path = "/Users/lachlan/Documents/iProjects/auto-publish/videos/IMG_5303/IMG_5303_highlighted.mp4"
    thumbnail_path = "/Users/lachlan/Documents/iProjects/auto-publish/videos/IMG_5303/IMG_5303_cover.jpg"
    metadata_file_path = "/Users/lachlan/Documents/iProjects/auto-publish/videos/IMG_5303/IMG_5303_metadata.json"

    with open(metadata_file_path, 'r') as file:
        metadata = json.load(file)

    # Your Chrome WebDriver options
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:5006")
    driver = webdriver.Chrome(options=options)
    test_mode = True

    # Create an instance of the ShiPinHaoPublisher
    shp_publisher = ShiPinHaoPublisher(
        driver=driver,
        video_path=video_path,
        thumbnail_path=thumbnail_path,
        metadata=metadata,
        test=test_mode  # Set to False to disable test mode
    )

    # Start publishing process
    shp_publisher.publish()
