import selenium
from selenium import webdriver
import pathlib
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, NoSuchWindowException, TimeoutException, NoAlertPresentException
from selenium.common.exceptions import WebDriverException, ElementClickInterceptedException, StaleElementReferenceException


from utils import dismiss_alert, bring_to_front, close_extra_tabs, safe_get
from login_douyin import DouyinLogin

import traceback
import os

from publish_verification import verify_publish_in_management


DOUYIN_MANAGEMENT_URL = "https://creator.douyin.com/creator-micro/content/manage"

class UploadFailedException(Exception):
    """Exception raised when the video upload fails."""
    def __init__(self, message="Video upload failed"):
        self.message = message
        super().__init__(self.message)

class DouyinPublisher:
    def __init__(self, driver, path_mp4, path_cover, metadata, test=False):
        self.driver = driver
        self.path_mp4 = path_mp4
        self.path_cover = path_cover
        self.metadata = metadata
        self.test = test
        self.retry_count = 0  # initialize retry count

        douyin_login = DouyinLogin(driver)
        douyin_login.check_and_act()

    def _find_first(self, xpaths, timeout=20, visible=True):
        condition = EC.visibility_of_element_located if visible else EC.presence_of_element_located
        last_exc = None
        for xpath in xpaths:
            try:
                return WebDriverWait(self.driver, timeout).until(condition((By.XPATH, xpath)))
            except Exception as exc:
                last_exc = exc
        if last_exc:
            raise last_exc

    def _find_any(self, xpaths, timeout=5, visible=True):
        for xpath in xpaths:
            try:
                condition = EC.visibility_of_element_located if visible else EC.presence_of_element_located
                WebDriverWait(self.driver, timeout).until(condition((By.XPATH, xpath)))
                return True
            except Exception:
                continue
        return False

    def _safe_click(self, element):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        except Exception:
            pass
        try:
            self.driver.execute_script(
                "const el = arguments[0]; setTimeout(() => el.click(), 0);",
                element,
            )
            time.sleep(0.5)
            return True
        except Exception:
            try:
                element.click()
                return True
            except Exception:
                return False

    def _click_first(self, xpaths, timeout=20):
        element = self._find_first(xpaths, timeout=timeout)
        if not self._safe_click(element):
            raise WebDriverException("Failed to click element.")

    def _click_any(self, xpaths, timeout=5):
        for xpath in xpaths:
            try:
                element = self._find_first([xpath], timeout=timeout)
                if self._safe_click(element):
                    return True
            except Exception:
                continue
        return False

    def _body_text(self):
        try:
            return self.driver.execute_script("return document.body ? document.body.innerText : '';") or ""
        except Exception:
            return ""

    def _resume_unpublished_draft_if_present(self):
        """Reuse Douyin's existing unpublished draft when the upload already exists.

        Douyin can leave a successful upload in a local/server draft if a later
        step fails. In that state the upload page shows "你还有上次未发布的视频".
        Starting a fresh upload wastes time and can create duplicate/stale
        drafts, so continue the draft before falling back to file upload.
        """
        body_text = self._body_text()
        prompt_present = "你还有上次未发布的视频" in body_text or "继续编辑" in body_text
        if not prompt_present:
            return False

        print("Douyin unpublished draft prompt detected; continuing existing draft.")
        self._click_first(
            [
                '//button[normalize-space()="继续编辑"]',
                '//*[normalize-space()="继续编辑"]/ancestor::button[1]',
                '//*[normalize-space()="继续编辑"]',
            ],
            timeout=10,
        )
        time.sleep(5)
        return True

    def _allow_draft_reuse(self):
        return os.environ.get("AUTOPUB_DOUYIN_REUSE_DRAFT", "0").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    def _replace_existing_draft_video(self, path_mp4):
        """Replace a resumed Douyin draft instead of publishing stale uploaded media."""
        print("Douyin draft reuse is disabled; replacing the draft video with the requested file.")
        self._click_any(
            [
                '//*[normalize-space()="重新上传"]',
                '//*[contains(text(),"重新上传")]/ancestor::button[1]',
                '//*[contains(text(),"替换视频")]/ancestor::button[1]',
                '//*[contains(text(),"替换视频")]',
            ],
            timeout=8,
        )
        time.sleep(3)
        self._upload_video_file(path_mp4)

    def _upload_video_file(self, path_mp4):
        print("Uploading video file to Douyin...")
        bring_to_front(["抖音"])
        video_input = self._find_first(
            [
                '//input[@type="file" and contains(@accept,"video")]',
                '//input[@type="file" and contains(@accept,"mp4")]',
                '//input[@type="file"]',
            ],
            timeout=30,
            visible=False,
        )
        video_input.send_keys(path_mp4)
        time.sleep(5)

    def _set_input_value(self, element, text):
        try:
            self.driver.execute_script(
                """
                const el = arguments[0];
                const value = arguments[1];
                const proto = Object.getPrototypeOf(el);
                const descriptor = Object.getOwnPropertyDescriptor(proto, 'value')
                  || Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')
                  || Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value');
                if (descriptor && descriptor.set) {
                    descriptor.set.call(el, value);
                } else {
                    el.value = value;
                }
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                """,
                element,
                text,
            )
            return
        except Exception:
            self.driver.execute_script(
                """
                const el = arguments[0];
                el.value = arguments[1];
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                """,
                element,
                text,
            )

    def _set_text(self, element, text):
        tag_name = ""
        try:
            tag_name = element.tag_name.lower()
        except Exception:
            pass
        if tag_name in ("input", "textarea"):
            self._set_input_value(element, text)
            return
        try:
            self.driver.execute_script(
                """
                const el = arguments[0];
                const value = arguments[1];
                el.focus();
                if (el.isContentEditable) {
                    el.innerText = value;
                } else {
                    el.textContent = value;
                }
                el.dispatchEvent(new InputEvent('input', {
                    bubbles: true,
                    inputType: 'insertText',
                    data: value
                }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                """,
                element,
                text,
            )
        except Exception:
            self.driver.execute_script(
                """
                const el = arguments[0];
                el.textContent = arguments[1];
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                """,
                element,
                text,
            )

    def _add_topics(self, tags):
        if not tags:
            return False
        try:
            topic_input = self._find_first(
                [
                    '//input[contains(@placeholder,"话题")]',
                    '//div[@data-placeholder="添加话题" and @contenteditable="true"]',
                    '//div[contains(@class,"topic") and @contenteditable="true"]',
                    '//*[contains(text(),"话题")]/..//input',
                ],
                timeout=3,
                visible=False,
            )
        except Exception:
            return False
        for tag in tags:
            cleaned = tag.strip().lstrip("#")
            if not cleaned:
                continue
            try:
                topic_input.click()
                topic_input.send_keys(f"#{cleaned}")
                time.sleep(0.5)
                topic_input.send_keys(Keys.ENTER)
                time.sleep(0.5)
            except Exception:
                continue
        return True

    def wait_for_element_to_be_clickable(self, xpath, timeout=600):
        time.sleep(3)  # your actual implementation


    def publish(self):
        if self.retry_count < 3:  # maximum 3 tries (initial + 2 retries)
            try:
                driver = self.driver
                path_mp4 = self.path_mp4
                path_cover = self.path_cover
                metadata = self.metadata
                test = self.test

                print("Starting the publishing process on Douyin...")
                safe_get(driver, "https://creator.douyin.com/creator-micro/content/upload", timeout=45, label="Douyin upload page")
                time.sleep(1)
                dismiss_alert(driver)
                time.sleep(10)

                bring_to_front(["抖音"])  # This should be defined somewhere in your code
                close_extra_tabs(driver)

                # Monitor upload status
                reupload_xpaths = [
                    '//*[text()="重新上传"]',
                    '//*[contains(text(),"替换视频")]',
                    '//*[contains(text(),"重新上传")]',
                    '//*[contains(text(),"上传完成")]',
                ]
                failure_xpaths = [
                    '//*[text()="上传失败，重新上传"]',
                    '//*[contains(text(),"上传失败")]',
                    '//*[contains(text(),"上传异常")]',
                ]

                resumed_draft = self._resume_unpublished_draft_if_present()
                draft_upload_failed = self._find_any(failure_xpaths, timeout=2, visible=False)
                if draft_upload_failed:
                    print("Existing Douyin draft has a failed upload; reuploading inside the draft.")
                    self._upload_video_file(path_mp4)
                elif resumed_draft and not self._allow_draft_reuse():
                    self._replace_existing_draft_video(path_mp4)
                elif resumed_draft or self._find_any(reupload_xpaths, timeout=5, visible=False):
                    print("Using existing Douyin draft/upload; skipping video upload.")
                else:
                    self._upload_video_file(path_mp4)

                print("Waiting for the video to be uploaded...")
                time.sleep(3)
                # WebDriverWait(driver, 3600).until(EC.presence_of_element_located((By.XPATH, '//*[text()="重新上传"]')))
                start_time = time.time()
                timeout = 3600  # 3600 seconds timeout
                
                while True:
                    if time.time() - start_time > timeout:
                        raise Exception("Timeout reached while waiting for video to be uploaded or for a failure message.")

                    if self._find_any(failure_xpaths, timeout=2, visible=False):
                        print("Upload failed! Raising an error to initiate retry...")
                        raise UploadFailedException("Upload failed due to presence of failure indicator.")

                    if self._find_any(reupload_xpaths, timeout=5, visible=False):
                        print("Video upload prompt detected, indicating upload completion.")
                        break

                    time.sleep(5)  # Wait a bit before checking again

                print("Skipping cover upload for Douyin.")
                time.sleep(2)

                 # Entering the title
                print("Entering the title...")
                title_input_element = self._find_first(
                    [
                        '//input[@placeholder="好的作品标题可获得更多浏览"]',
                        '//input[contains(@placeholder,"标题")]',
                        '//div[contains(@class,"title") or contains(@class,"Title")]//input',
                    ],
                    timeout=30,
                )
                time.sleep(1)
                title_text = (metadata.get("title") or "").strip()[:30]
                self._set_input_value(title_input_element, title_text)



                print("Entering video description...")
                description_input_element = self._find_first(
                    [
                        '//div[@data-placeholder="添加作品简介"]',
                        '//div[@contenteditable="true" and contains(@data-placeholder,"简介")]',
                        '//textarea[contains(@placeholder,"简介")]',
                        '//div[@contenteditable="true"]',
                    ],
                    timeout=30,
                )
                tags = [tag.strip().lstrip("#") for tag in metadata.get("tags", []) if tag and tag.strip()]
                # Douyin's separate topic widget is optional and can wedge the
                # browser on send_keys. Keep hashtags in the description, which
                # is enough for publishing and avoids blocking the queue.
                topics_added = False
                extra_tags = ["上热门", "dou上热门", "我要上热门"]
                if topics_added:
                    combined_tags = extra_tags
                else:
                    combined_tags = tags + extra_tags
                description_text = (metadata.get("long_description") or metadata.get("brief_description") or "").strip()
                tag_text = " ".join([f"#{tag}" for tag in combined_tags if tag])
                description_with_tags = f"{description_text} {tag_text}".strip()
                time.sleep(1)
                self._set_text(description_input_element, description_with_tags[:1000])


                try:
                    print("Entering location information...")
                    time.sleep(3)
                    # wait_for_element_to_be_clickable(driver, '//*[text()="输入地理位置"]')
                    driver.find_element(By.XPATH, '//*[text()="输入地理位置"]').click()
                    time.sleep(3)
                    # wait_for_element_to_be_clickable(driver, '//*[text()="输入地理位置"]/..//input')
                    driver.find_element(By.XPATH, '//*[text()="输入地理位置"]/..//input').send_keys("香港大学")
                    time.sleep(3)
                    # wait_for_element_to_be_clickable(driver, '//*[@class="semi-popover-content"]//*[text()="香港大学"]')
                    driver.find_element(By.XPATH, '//*[@class="semi-popover-content"]//*[text()="香港大学"]').click()
                except:
                    print("Cannot select location!")
                    pass


                

                # JavaScript code as a multi-line Python string
                script = """
                let elementsWithText = Array.from(document.querySelectorAll("div")).filter(el => el.textContent.includes('原创内容'));
                let targetSwitch;

                elementsWithText.forEach(el => {
                    let switchElement = el.parentElement.querySelector("input[type='checkbox'][role='switch']");
                    if (switchElement) {
                        targetSwitch = switchElement;
                    }
                });

                if (targetSwitch) {
                    // Return information about the switch to the Python context
                    return {
                        found: true,
                        currentState: targetSwitch.checked ? "ON" : "OFF"
                    };
                } else {
                    return {
                        found: false
                    };
                }
                """

                # Execute the script
                result = driver.execute_script(script)

                # Handle the result
                if result['found']:
                    print("Found '原创内容' switch.")
                    print("Current state of '原创内容' switch:", result['currentState'])

                    if result['currentState'] == "OFF":
                        toggle_script = """
                        let elementsWithText = Array.from(document.querySelectorAll("div")).filter(el => el.textContent.includes('原创内容'));
                        let targetSwitch;

                        elementsWithText.forEach(el => {
                            let switchElement = el.parentElement.querySelector("input[type='checkbox'][role='switch']");
                            if (switchElement) {
                                targetSwitch = switchElement;
                            }
                        });

                        if (targetSwitch) {
                            targetSwitch.click();
                        }
                        """
                        time.sleep(3)
                        driver.execute_script(toggle_script)
                        print("Enabled the '原创内容' switch.")
                else:
                    print("Could not find '原创内容' switch.")

                # Final steps for publishing
                if test:
                    user_input = input("Do you want to publish now? Type 'yes' to confirm: ").strip().lower()
                else:
                    user_input = "yes"
                if user_input == 'yes':
                    print("Publishing the video...")
                    time.sleep(3)
                    self._click_first(
                        [
                            '//button[.//*[contains(text(),"发布")]]',
                            '//button[contains(text(),"发布")]',
                            '//*[contains(text(),"发布")]/ancestor::button[1]',
                        ],
                        timeout=20,
                    )
                    time.sleep(10)
                    dismiss_alert(driver)
                    time.sleep(3)
                    verify_publish_in_management(
                        driver,
                        DOUYIN_MANAGEMENT_URL,
                        metadata,
                        platform_name="Douyin",
                        timeout=int(os.environ.get("AUTOPUB_DOUYIN_VERIFY_TIMEOUT", "240")),
                    )
                    print("Video published successfully!")
                else:
                    print("Publishing cancelled by the user.")
                
                self.retry_count = 0  # reset retry count after successful execution
                return True
            except Exception as e:
                print(f"An error occurred: {e}")
                traceback.print_exc()
                self.retry_count += 1
                print(f"Retrying the whole process... Attempt {self.retry_count}")
                return self.publish()  # Retry the whole process
        else:
            raise RuntimeError("Maximum retry attempts reached. Douyin process failed.")

# Rest of your code for initialization and running the publisher
def get_media_paths(catalog):
    path = pathlib.Path(catalog)
    path_mp4 = next((str(p) for p in path.glob('*.mp4')), None)
    path_cover = next((str(p) for p in path.glob('*') if p.suffix in ['.png', '.jpg']), None)
    return path_mp4, path_cover

if __name__ == "__main__":
    # Constants
    catalog_mp4 = r"/Users/lachlan/Documents/iProjects/auto-publish/videos"
    chrome_driver_path = "/user/local/bin/chromedriver"  # Change this to your Chromedriver path

    # Initialize Chrome options
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:5003")
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
            "middle_description": "跟随我们的味蕾之旅，发现为何这款烤鸡让人赞不绝口！",
            "long_description": "跟随我们的味蕾之旅，发现为何这款烤鸡让人赞不绝口！",
            "tags": ["美食", "烤鸡", "推荐"]
        }

        # Create an instance of the DouyinPublisher
        pub_douyinlisher = DouyinPublisher(
            driver=driver,
            path_mp4=path_mp4,
            path_cover=path_cover,
            metadata=metadata
        )

        # Start publishing process
        pub_douyinlisher.publish()
