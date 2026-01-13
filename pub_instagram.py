import time
import traceback

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from utils import dismiss_alert, bring_to_front
from login_instagram import InstagramLogin


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
        element.click()
        return element

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

    def _build_caption(self):
        title = (self.metadata.get("title") or "").strip()
        desc = (self.metadata.get("long_description") or "").strip()
        if not desc:
            desc = (self.metadata.get("brief_description") or "").strip()
        tags = self.metadata.get("tags") or []
        tag_text = " ".join([f"#{tag}" for tag in tags if tag])
        parts = [part for part in [title, desc, tag_text] if part]
        caption = "\n\n".join(parts)
        return caption[:2200]

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

    def _click_next_until_caption(self, max_clicks=2):
        driver = self.driver
        for _ in range(max_clicks):
            if driver.find_elements(By.XPATH, "//div[@aria-label='Write a caption...']"):
                return
            if driver.find_elements(By.XPATH, "//textarea[@aria-label='Write a caption...']"):
                return
            try:
                self._click_xpath("//div[@role='button' and normalize-space()='Next']", timeout=20)
            except Exception:
                self._click_xpath("//button[normalize-space()='Next']", timeout=20)
            time.sleep(2)

    def publish(self):
        if self.retry_count >= 3:
            return

        try:
            driver = self.driver
            print("Starting the publishing process on Instagram...")
            driver.get("https://www.instagram.com/")
            time.sleep(2)
            dismiss_alert(driver)
            time.sleep(2)
            bring_to_front(["Instagram"])

            create_button = self._find_first(
                [
                    "//span[normalize-space()='Create']/ancestor::*[self::a or self::button or self::div[@role='button']]",
                    "//svg[@aria-label='New post']/ancestor::*[self::a or self::button or self::div[@role='button']]",
                ],
                timeout=20,
            )
            driver.execute_script("arguments[0].click();", create_button)
            time.sleep(1)

            post_button = self._find_first(
                [
                    "//span[normalize-space()='Post']/ancestor::*[self::a or self::button or self::div[@role='button']]",
                    "//span[normalize-space()='Post']",
                ],
                timeout=20,
            )
            driver.execute_script("arguments[0].click();", post_button)
            time.sleep(2)

            self._upload_video()

            self._click_next_until_caption(max_clicks=2)

            caption = self._build_caption()
            if caption:
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

            try:
                self._click_xpath("//div[@role='button' and normalize-space()='Share']", timeout=30)
            except Exception:
                self._click_xpath("//button[normalize-space()='Share']", timeout=30)

            print("Instagram publish triggered.")
        except Exception as exc:
            self.retry_count += 1
            print(f"Instagram publish failed: {exc}")
            traceback.print_exc()
            if self.retry_count < 3:
                time.sleep(10)
                self.publish()
