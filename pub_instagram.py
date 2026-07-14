import json
import os
import time
import traceback
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

from utils import dismiss_alert, bring_to_front, close_extra_tabs
from login_instagram import InstagramLogin

try:
    from publish_routing import infer_publish_category
except Exception:
    infer_publish_category = None


def _load_metadata_from_dir(metadata_dir: Path):
    if not metadata_dir or not metadata_dir.exists():
        return {}

    if metadata_dir.is_file():
        try:
            return json.loads(metadata_dir.read_text(encoding="utf-8"))
        except Exception:
            traceback.print_exc()
            return {}

    candidates = []
    for lang_dir in ("en", "zh"):
        lang_path = metadata_dir / lang_dir
        if not lang_path.exists():
            continue
        for path in sorted(lang_path.glob("*.json")):
            candidates.append(path)

    if not candidates:
        candidates = sorted(metadata_dir.glob("*.json"))

    for path in candidates:
        if path.name.endswith("_metadata_en.json"):
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                traceback.print_exc()
                return {}

    for path in candidates:
        if path.name.endswith("_metadata_zh.json"):
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                traceback.print_exc()
                return {}

    if candidates:
        try:
            return json.loads(candidates[0].read_text(encoding="utf-8"))
        except Exception:
            traceback.print_exc()
            return {}

    return {}


def remove_non_bmp(text):
    return "".join(ch for ch in (text or "") if ord(ch) <= 0xFFFF)


class InstagramPublisher:
    def __init__(self, driver, path_mp4, path_cover, metadata, test=False):
        self.driver = driver
        self.path_mp4 = path_mp4
        self.path_cover = path_cover
        self.metadata = metadata or {}
        self.test = test
        self.retry_count = 0

        InstagramLogin(driver).check_and_act()

    def _click_xpath(self, xpath, timeout=30):
        driver = self.driver
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        try:
            element.click()
        except ElementClickInterceptedException:
            self._dismiss_reels_dialog(timeout=6)
            driver.execute_script("arguments[0].click();", element)
        return element

    def _safe_click(self, element):
        driver = self.driver
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        except Exception:
            pass
        try:
            element.click()
            return True
        except ElementClickInterceptedException:
            self._dismiss_reels_dialog(timeout=6)
        except Exception:
            pass
        try:
            driver.execute_script("arguments[0].click();", element)
            return True
        except Exception:
            return False

    def _find_first(self, xpaths, timeout=10):
        driver = self.driver
        end_time = time.time() + timeout
        last_exc = None
        while time.time() < end_time:
            for xpath in xpaths:
                try:
                    element = driver.find_element(By.XPATH, xpath)
                    return element
                except Exception as exc:
                    last_exc = exc
            time.sleep(1)
        if last_exc:
            raise last_exc
        raise TimeoutException("Element not found")

    def _caption_present(self):
        driver = self.driver
        return bool(
            driver.find_elements(By.XPATH, "//div[@aria-label='Write a caption...']")
            or driver.find_elements(By.XPATH, "//textarea[@aria-label='Write a caption...']")
        )

    def _get_create_dialog(self):
        driver = self.driver
        dialog_candidates = [
            "//div[@role='dialog' and @aria-label='Create new post']",
            "//div[@role='dialog' and .//div[@aria-label='Write a caption...']]",
            "//div[@role='dialog' and .//textarea[@aria-label='Write a caption...']]",
        ]
        for xpath in dialog_candidates:
            dialogs = driver.find_elements(By.XPATH, xpath)
            if dialogs:
                return dialogs[0]
        return None

    def _upload_dialog_present(self):
        driver = self.driver
        return bool(
            driver.find_elements(
                By.XPATH,
                "//div[@role='dialog' and .//input[@type='file']]",
            )
            or driver.find_elements(
                By.XPATH,
                "//div[@role='dialog' and .//button[normalize-space()='Select From Computer']]",
            )
            or driver.find_elements(By.XPATH, "//input[@type='file']")
        )

    def _dismiss_reels_dialog(self, timeout=8):
        driver = self.driver
        dialog_xpath = "//div[@role='dialog']"
        ok_xpaths = [
            "//div[@role='dialog']//button[normalize-space()='OK']",
            "//div[@role='dialog']//div[@role='button' and normalize-space()='OK']",
        ]
        start_time = time.time()
        while time.time() - start_time < timeout:
            for xpath in ok_xpaths:
                buttons = driver.find_elements(By.XPATH, xpath)
                for button in buttons:
                    try:
                        driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});",
                            button,
                        )
                        button.click()
                        time.sleep(1)
                        return True
                    except Exception:
                        try:
                            driver.execute_script("arguments[0].click();", button)
                            time.sleep(1)
                            return True
                        except Exception:
                            pass
            if not driver.find_elements(By.XPATH, dialog_xpath):
                return False
            time.sleep(1)
        return False

    def _share_sheet_present(self):
        driver = self.driver
        return bool(
            driver.find_elements(By.XPATH, "//h2//span[normalize-space()='Share']")
            or driver.find_elements(By.XPATH, "//div[@role='button' and normalize-space()='Send']")
        )

    def _close_share_sheet(self):
        driver = self.driver
        close_xpaths = [
            "//div[@role='button' and @aria-label='Close']",
            "//svg[@aria-label='Close']/ancestor::*[@role='button']",
        ]
        for xpath in close_xpaths:
            buttons = driver.find_elements(By.XPATH, xpath)
            for button in buttons:
                try:
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});",
                        button,
                    )
                    button.click()
                    return True
                except Exception:
                    try:
                        driver.execute_script("arguments[0].click();", button)
                        return True
                    except Exception:
                        pass
        return False

    def _spinner_present(self):
        driver = self.driver
        return bool(
            driver.find_elements(By.XPATH, "//img[@alt='Spinner placeholder']")
            or driver.find_elements(By.XPATH, "//img[contains(@src,'ShFi4iY4Fd9.gif')]")
        )

    def _publish_success_present(self):
        driver = self.driver
        return bool(
            driver.find_elements(By.XPATH, "//h3[normalize-space()='Your reel has been shared.']")
            or driver.find_elements(By.XPATH, "//div[normalize-space()='Your reel has been shared.']")
            or driver.find_elements(By.XPATH, "//img[@alt='Animated checkmark']")
            or driver.find_elements(By.XPATH, "//img[contains(@src,'sHkePOqEDPz.gif')]")
        )

    def _build_caption(self):
        def build_from(meta):
            if not isinstance(meta, dict):
                return ""
            title = (meta.get("title") or "").strip()
            desc = (meta.get("long_description") or "").strip()
            if not desc:
                desc = (meta.get("brief_description") or "").strip()
            tags = meta.get("tags") or []
            tag_text = " ".join([f"#{tag}" for tag in tags if tag])
            parts = [part for part in [title, desc, tag_text] if part]
            return "\n\n".join(parts).strip()

        en_meta = self.metadata.get("english_version")
        en_caption = build_from(en_meta) if isinstance(en_meta, dict) else ""
        zh_caption = build_from(self.metadata)

        if en_caption and zh_caption and zh_caption != en_caption:
            caption = f"{en_caption}\n\n{zh_caption}"
        else:
            caption = en_caption or zh_caption

        return remove_non_bmp(caption)[:2200]

    def _log_category_routing(self):
        if infer_publish_category is None:
            return
        category, reason = infer_publish_category(self.metadata, media_kind="video")
        print(
            "Instagram publish category metadata: "
            f"{category} ({reason}); Instagram web upload has no stable "
            "per-post category/playlist field, so no category UI is selected."
        )

    def _upload_video(self):
        driver = self.driver
        inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
        target = None
        for inp in inputs:
            accept = (inp.get_attribute("accept") or "").lower()
            if "video" in accept or "mp4" in accept or "quicktime" in accept:
                target = inp
                break
        if target is None and inputs:
            target = inputs[0]
        if not target:
            raise TimeoutException("Upload input not found")
        target.send_keys(self.path_mp4)

    def _open_crop_menu(self, timeout=10):
        driver = self.driver
        video_xpaths = [
            "//div[@role='dialog']//video",
            "//video",
        ]
        crop_button_xpaths = [
            "//svg[@aria-label='Select Crop']/ancestor::*[self::button or self::div[@role='button']][1]",
            "//title[normalize-space()='Select Crop']/ancestor::*[name()='svg'][1]"
            "/ancestor::*[self::button or self::div[@role='button']][1]",
            "//svg[@aria-label='Select Crop']",
        ]
        end_time = time.time() + timeout
        while time.time() < end_time:
            for xpath in video_xpaths:
                videos = driver.find_elements(By.XPATH, xpath)
                if videos:
                    self._safe_click(videos[0])
                    break
            for xpath in crop_button_xpaths:
                buttons = driver.find_elements(By.XPATH, xpath)
                if not buttons:
                    continue
                print(f"Found crop button(s) for xpath: {xpath} -> {len(buttons)}")
                if self._safe_click(buttons[0]):
                    return True
                try:
                    driver.execute_script("arguments[0].click();", buttons[0])
                    return True
                except Exception:
                    pass
            try:
                clicked = driver.execute_script(
                    """
                    const svgs = Array.from(document.querySelectorAll('svg[aria-label="Select Crop"]'));
                    if (!svgs.length) return false;
                    let svg = svgs.find(el => el.closest('[role="dialog"]')) || svgs[0];
                    let button = svg.closest('button,[role="button"]') || svg.parentElement;
                    if (!button) return false;
                    button.click();
                    return true;
                    """
                )
                if clicked:
                    print("Opened crop menu via JS querySelector.")
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        print("Crop menu button not found.")
        return False

    def _set_crop_original(self, timeout=20):
        driver = self.driver
        print("Attempting to set crop to Original...")
        original_xpaths = [
            "//div[@role='dialog']//span[normalize-space()='Original']/ancestor::*[self::button or self::div[@role='button']][1]",
            "//span[normalize-space()='Original']/ancestor::*[self::button or self::div[@role='button']][1]",
        ]
        selected_original_xpaths = [
            "//div[@role='dialog']//span[normalize-space()='Original']"
            "/ancestor::*[@aria-checked='true' or @aria-selected='true'][1]",
        ]
        end_time = time.time() + timeout
        while time.time() < end_time:
            self._dismiss_reels_dialog(timeout=2)
            for xpath in selected_original_xpaths:
                if driver.find_elements(By.XPATH, xpath):
                    print("Crop already set to Original.")
                    return True
            for xpath in original_xpaths:
                buttons = driver.find_elements(By.XPATH, xpath)
                if buttons:
                    print(f"Found Original option(s) for xpath: {xpath} -> {len(buttons)}")
                if buttons and self._safe_click(buttons[0]):
                    print("Selected crop: Original.")
                    time.sleep(0.5)
                    return True
            if self._open_crop_menu(timeout=2):
                print("Opened crop menu.")
                time.sleep(1)
            time.sleep(1)
        print("Failed to set crop to Original (timeout).")
        return False

    def _wait_for_crop_original(self, timeout=None):
        """Wait for Instagram's crop controls and require the Original option.

        ``send_keys`` returns before large videos have finished loading into the
        editor.  Advancing while the crop control is still unavailable makes
        Instagram apply its default crop.  Keep the dialog on the crop stage
        until Original can actually be selected.
        """
        if timeout is None:
            try:
                timeout = int(os.getenv("AUTOPUB_INSTAGRAM_CROP_TIMEOUT", "900"))
            except (TypeError, ValueError):
                timeout = 900
        timeout = max(30, timeout)
        deadline = time.time() + timeout
        attempt = 0
        while time.time() < deadline:
            attempt += 1
            remaining = max(1, int(deadline - time.time()))
            if self._set_crop_original(timeout=min(25, remaining)):
                print(f"Instagram Original crop confirmed on attempt {attempt}.")
                return True
            if self._caption_present():
                print("Instagram advanced past the crop stage before Original was selected.")
                return False
            print(
                "Instagram crop controls are not ready yet; "
                f"waiting with {remaining}s remaining."
            )
            time.sleep(min(5, remaining))
        print("Instagram Original crop was not available before the timeout.")
        return False

    def _click_next_until_caption(self, max_clicks=2):
        driver = self.driver
        for idx in range(max_clicks):
            self._dismiss_reels_dialog(timeout=4)
            if self._caption_present():
                print("Caption screen detected.")
                return
            try:
                print(f"Clicking Next ({idx + 1}/{max_clicks})...")
                self._click_xpath("//div[@role='button' and normalize-space()='Next']", timeout=20)
            except Exception:
                print(f"Clicking Next (button) ({idx + 1}/{max_clicks})...")
                self._click_xpath("//button[normalize-space()='Next']", timeout=20)
            time.sleep(2)
        if not self._caption_present():
            raise TimeoutException("Instagram caption screen was not reached")

    def _publish_verification_terms(self):
        terms = []
        for meta in (self.metadata.get("english_version"), self.metadata):
            if not isinstance(meta, dict):
                continue
            for key in ("title", "brief_description"):
                value = str(meta.get(key) or "").strip()
                if len(value) >= 6 and value not in terms:
                    terms.append(value)
        return terms

    def _verify_latest_profile_post(self, timeout=60):
        """Verify an uncertain Share result against the newest profile post."""
        driver = self.driver
        profile_xpaths = [
            "//a[@href and .//span[normalize-space()='Profile']]",
            "//a[@href and .//*[name()='svg' and @aria-label='Profile']]",
        ]
        profile_url = None
        for xpath in profile_xpaths:
            for element in driver.find_elements(By.XPATH, xpath):
                href = element.get_attribute("href")
                if href:
                    profile_url = href
                    break
            if profile_url:
                break
        if not profile_url:
            print("Instagram profile URL was not available for fallback verification.")
            return False

        try:
            driver.get(profile_url)
            WebDriverWait(driver, timeout).until(
                lambda d: d.find_elements(
                    By.XPATH,
                    "//main//a[contains(@href, '/reel/') or contains(@href, '/p/')]",
                )
            )
            latest = driver.find_elements(
                By.XPATH,
                "//main//a[contains(@href, '/reel/') or contains(@href, '/p/')]",
            )[0]
            latest_url = latest.get_attribute("href")
            if latest_url:
                driver.get(latest_url)
            WebDriverWait(driver, timeout).until(
                lambda d: d.find_elements(By.TAG_NAME, "body")
            )
            body_text = driver.find_element(By.TAG_NAME, "body").text
            normalized_body = "".join(body_text.split())
            for term in self._publish_verification_terms():
                if term in body_text or "".join(term.split()) in normalized_body:
                    print(f"Instagram profile verification matched: {term!r}")
                    return True
        except Exception as exc:
            print(f"Instagram profile verification failed: {exc}")
            return False

        print("Instagram newest profile post did not match this publish package.")
        return False

    def _click_share_button(self):
        dialog = self._get_create_dialog()
        if dialog:
            for xpath in (
                ".//div[@role='button' and normalize-space()='Share']",
                ".//button[normalize-space()='Share']",
            ):
                try:
                    button = dialog.find_element(By.XPATH, xpath)
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});",
                        button,
                    )
                    try:
                        button.click()
                    except ElementClickInterceptedException:
                        self._dismiss_reels_dialog(timeout=6)
                        self.driver.execute_script("arguments[0].click();", button)
                    return True
                except Exception:
                    pass

        try:
            self._click_xpath("//div[@role='button' and normalize-space()='Share']", timeout=30)
        except Exception:
            self._click_xpath("//button[normalize-space()='Share']", timeout=30)
        return True

    def _wait_for_publish_complete(self, timeout=600):
        start_time = time.time()
        while time.time() - start_time < timeout:
            self._dismiss_reels_dialog(timeout=2)
            if self._publish_success_present():
                return True
            if self._share_sheet_present():
                self._close_share_sheet()
            if self._spinner_present():
                time.sleep(2)
                continue
            if not self._caption_present() and not self._get_create_dialog():
                time.sleep(2)
                continue
            time.sleep(2)
        return False

    def publish(self):
        if self.retry_count >= 3:
            return False

        share_clicked = False

        try:
            driver = self.driver
            print("Starting the publishing process on Instagram...")
            driver.get("https://www.instagram.com/")
            time.sleep(2)
            dismiss_alert(driver)
            time.sleep(2)
            bring_to_front(["Instagram"])
            close_extra_tabs(driver)
            self._log_category_routing()

            create_button = self._find_first(
                [
                    "//span[normalize-space()='Create']/ancestor::*[self::a or self::button or self::div[@role='button']]",
                    "//svg[@aria-label='New post']/ancestor::*[self::a or self::button or self::div[@role='button']]",
                ],
                timeout=20,
            )
            driver.execute_script("arguments[0].click();", create_button)
            time.sleep(1)

            if not self._upload_dialog_present():
                try:
                    post_button = self._find_first(
                        [
                            "//span[normalize-space()='Post']/ancestor::*[self::a or self::button or self::div[@role='button']]",
                            "//span[normalize-space()='Post']",
                        ],
                        timeout=12,
                    )
                    driver.execute_script("arguments[0].click();", post_button)
                    time.sleep(2)
                except Exception:
                    if not self._upload_dialog_present():
                        raise

            WebDriverWait(driver, 30).until(
                lambda d: d.find_elements(By.XPATH, "//input[@type='file']")
            )
            bring_to_front(["Instagram"])
            self._upload_video()

            self._dismiss_reels_dialog(timeout=10)
            crop_set = self._wait_for_crop_original()
            print(f"Crop set to Original: {crop_set}")
            if not crop_set:
                raise RuntimeError(
                    "Instagram Original crop could not be confirmed; "
                    "refusing to publish a cropped video"
                )

            self._click_next_until_caption(max_clicks=2)

            caption = self._build_caption()
            if caption:
                print(f"Adding caption ({len(caption)} chars)...")
                try:
                    caption_box = WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Write a caption...']"))
                    )
                    caption_box.click()
                    caption_box.send_keys(caption)
                except Exception:
                    caption_box = WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.XPATH, "//textarea[@aria-label='Write a caption...']"))
                    )
                    caption_box.click()
                    caption_box.send_keys(caption)
            else:
                print("No caption found in metadata.")

            print("Clicking Share...")
            self._click_share_button()
            share_clicked = True

            print("Waiting for publish confirmation...")
            if self._wait_for_publish_complete():
                print("Instagram publish confirmed.")
                return True
            print("Instagram publish confirmation timed out; checking the profile.")
            if self._verify_latest_profile_post():
                print("Instagram publish confirmed from the latest profile post.")
                return True
            print("Instagram publish could not be confirmed.")
            return False
        except Exception as exc:
            self.retry_count += 1
            print(f"Instagram publish failed: {exc}")
            traceback.print_exc()
            if self.retry_count < 3 and not share_clicked:
                time.sleep(10)
                return self.publish()
            return False


if __name__ == "__main__":
    path_mp4 = (
        "/home/lachlan/ProjectsLFS/lazyedit/DATA/IMG_7930_2026_01_04_01_05_56_COMPLETED/"
        "IMG_7930_2026_01_04_01_05_56_COMPLETED_subtitles.mp4"
    )
    metadata_dir = Path(
        "/home/lachlan/ProjectsLFS/lazyedit/DATA/IMG_7930_2026_01_04_01_05_56_COMPLETED/metadata"
    )

    if not os.path.exists(path_mp4):
        raise FileNotFoundError(f"Video not found: {path_mp4}")

    metadata = _load_metadata_from_dir(metadata_dir)
    if not metadata:
        metadata = {"title": Path(path_mp4).stem}

    login = InstagramLogin()
    publisher = InstagramPublisher(
        driver=login.driver,
        path_mp4=path_mp4,
        path_cover=None,
        metadata=metadata,
        test=True,
    )
    publisher.publish()
