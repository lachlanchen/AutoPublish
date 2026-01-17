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


from utils import dismiss_alert, bring_to_front, close_extra_tabs
from login_douyin import DouyinLogin

import traceback

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
            element.click()
            return True
        except (ElementClickInterceptedException, StaleElementReferenceException):
            try:
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except Exception:
                return False

    def _click_first(self, xpaths, timeout=20):
        element = self._find_first(xpaths, timeout=timeout)
        if not self._safe_click(element):
            raise WebDriverException("Failed to click element.")

    def _set_input_value(self, element, text):
        try:
            element.clear()
        except Exception:
            try:
                element.send_keys(Keys.CONTROL, "a")
                element.send_keys(Keys.BACKSPACE)
            except Exception:
                pass
        element.send_keys(text)

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
                if (document.execCommand) {
                    document.execCommand('selectAll', false, null);
                    document.execCommand('insertText', false, value);
                } else {
                    el.textContent = value;
                }
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                """,
                element,
                text,
            )
        except Exception:
            try:
                element.click()
                element.send_keys(text)
            except Exception:
                pass

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
                driver.get("https://creator.douyin.com/creator-micro/content/upload")
                time.sleep(1)
                dismiss_alert(driver)
                time.sleep(10)

                bring_to_front(["抖音"])  # This should be defined somewhere in your code
                close_extra_tabs(driver)

                # Uploading the video
                print("Uploading video...")
                time.sleep(3)
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

                # Monitor upload status
                print("Waiting for the video to be uploaded...")
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
                time.sleep(3)
                # WebDriverWait(driver, 3600).until(EC.presence_of_element_located((By.XPATH, '//*[text()="重新上传"]')))
                start_time = time.time()
                timeout = 3600  # 3600 seconds timeout
                
                while True:
                    if time.time() - start_time > timeout:
                        raise Exception("Timeout reached while waiting for video to be uploaded or for a failure message.")

                    if self._find_any(reupload_xpaths, timeout=5, visible=False):
                        print("Video upload prompt detected, indicating upload completion.")
                        break

                    if self._find_any(failure_xpaths, timeout=2, visible=False):
                        print("Upload failed! Raising an error to initiate retry...")
                        raise UploadFailedException("Upload failed due to presence of failure indicator.")


                    time.sleep(5)  # Wait a bit before checking again

                print("Adding cover...")
                time.sleep(3)
                self._click_first(
                    [
                        '//button[.//*[contains(text(),"选择封面")] or contains(text(),"选择封面")]',
                        '//*[text()="选择封面"]',
                        '//*[contains(text(),"编辑封面")]',
                        '//*[contains(text(),"更换封面")]',
                    ],
                    timeout=30,
                )
                time.sleep(3)
                try:
                    self._click_first(
                        [
                            '//*[@role="dialog"]//*[contains(text(),"上传封面")]',
                            '//*[@role="dialog"]//*[contains(text(),"上传图片")]',
                            '//*[@role="dialog"]//*[contains(text(),"上传")]',
                            '//*[contains(text(),"上传封面")]',
                        ],
                        timeout=10,
                    )
                except Exception:
                    pass
                time.sleep(3)
                cover_input = self._find_first(
                    [
                        '//*[text()="点击上传 或直接将图片文件拖入此区域"]/../../../..//input[@type="file"]',
                        '//*[@role="dialog"]//input[@type="file" and contains(@accept,"image")]',
                        '//*[@role="dialog"]//input[@type="file" and (contains(@accept,"png") or contains(@accept,"jpg") or contains(@accept,"jpeg"))]',
                        '//input[@type="file" and contains(@accept,"image")]',
                    ],
                    timeout=20,
                    visible=False,
                )
                cover_input.send_keys(path_cover)

                

                time.sleep(5)


                # JavaScript code as a multi-line Python string
                click_finish_button_script = """
                let buttons = Array.from(document.querySelectorAll("button.semi-button-primary.semi-button-light.finish--3_3_P"));
                let finishButton = buttons.find(btn => btn.textContent.includes('完成'));

                if (finishButton) {
                    // Scroll the button into view
                    finishButton.scrollIntoView(true);
                    
                    // Click the '完成' button
                    finishButton.click();
                    return true;
                } else {
                    return false;
                }
                """

                try:
                    self._click_first(
                        [
                            '//button[contains(text(),"完成")]',
                            '//button[.//*[contains(text(),"完成")]]',
                            '//button[contains(text(),"确定")]',
                            '//button[.//*[contains(text(),"确定")]]',
                        ],
                        timeout=15,
                    )
                    print("Clicked the '完成' button successfully.")
                except Exception:
                    button_clicked = driver.execute_script(click_finish_button_script)
                    if button_clicked:
                        print("Clicked the '完成' button successfully.")
                    else:
                        print("Could not find the '完成' button.")

                time.sleep(5)


                # JavaScript code to define and call the clickCloseButton function
                click_close_button_js = """
                function clickCloseButton() {
                    // Select the close button based on the class starting text
                    const closeButton = document.querySelector('svg[class^="close--"]');

                    // Check if the close button is found
                    if (closeButton) {
                        // Create a new click event
                        var clickEvent = new MouseEvent("click", {
                            view: window,
                            bubbles: true,
                            cancelable: false
                        });
                        
                        // Dispatch the event on the close button
                        closeButton.dispatchEvent(clickEvent);
                        return 'Close button clicked.';
                    } else {
                        return 'Close button not found.';
                    }
                }

                // Call the function to click the close button
                return clickCloseButton();
                """

                try:
                    # Execute the JavaScript code
                    result = driver.execute_script(click_close_button_js)
                    print(result)
                except WebDriverException as e:
                    print(f"WebDriverException occurred: {e}")

                time.sleep(3)

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
                topics_added = self._add_topics(tags)
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
                    print("Video published successfully!")
                else:
                    print("Publishing cancelled by the user.")
                
                self.retry_count = 0  # reset retry count after successful execution
            except Exception as e:
                print(f"An error occurred: {e}")
                traceback.print_exc()
                self.retry_count += 1
                print(f"Retrying the whole process... Attempt {self.retry_count}")
                self.publish()  # Retry the whole process
        else:
            print("Maximum retry attempts reached. Process failed.")

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
