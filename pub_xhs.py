import selenium
from selenium import webdriver
import pathlib
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchWindowException, TimeoutException
import time

from utils import dismiss_alert, bring_to_front, close_extra_tabs
from login_xiaohongshu import XiaoHongShuLogin

import traceback


class XiaoHongShuPublisher:
    def __init__(self, driver, path_mp4, path_cover, metadata, test=False):
        self.driver = driver
        self.path_mp4 = path_mp4
        self.path_cover = path_cover
        self.metadata = metadata
        self.test = test
        self.retry_count = 0  # initialize retry count


        xhs_login = XiaoHongShuLogin(driver)
        xhs_login.check_and_act()

    def _find_first(self, xpaths, timeout=20, visible=True):
        last_exc = None
        condition = EC.visibility_of_element_located if visible else EC.presence_of_element_located
        for xpath in xpaths:
            try:
                return WebDriverWait(self.driver, timeout).until(condition((By.XPATH, xpath)))
            except Exception as exc:
                last_exc = exc
        if last_exc:
            raise last_exc

    def _find_present(self, xpaths, visible=True):
        for xpath in xpaths:
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
            except Exception:
                continue
            for element in elements:
                try:
                    if not visible or element.is_displayed():
                        return element, xpath
                except Exception:
                    continue
        return None, None

    def _wait_for_upload_ready(self, timeout=3600):
        success_xpaths = [
            '//span[contains(@class,"video-plugin-title-action") and contains(normalize-space(),"重新上传")]',
            '//*[contains(@class,"video-plugin-title-action") and contains(normalize-space(),"重新上传")]',
            '//*[contains(text(),"重新上传")]',
            '//*[contains(text(),"替换视频")]',
            '//input[@placeholder="填写标题会有更多赞哦"]',
            '//input[@placeholder="填写标题会有更多赞哦～"]',
            '//div[contains(@class,"tiptap") and @contenteditable="true"]',
            '//div[contains(@class,"ProseMirror") and @contenteditable="true"]',
        ]
        failure_xpaths = [
            '//*[contains(text(),"上传失败")]',
            '//*[contains(text(),"上传出错")]',
            '//*[contains(text(),"上传异常")]',
        ]

        start_time = time.time()
        while time.time() - start_time <= timeout:
            failure_element, failure_xpath = self._find_present(failure_xpaths)
            if failure_element is not None:
                raise Exception(f"Video upload failed: matched {failure_xpath}")

            success_element, success_xpath = self._find_present(success_xpaths)
            if success_element is not None:
                print(f"Video uploaded successfully! Matched {success_xpath}")
                return success_element

            print("Waiting for the video to upload or for the editor to become ready...")
            time.sleep(5)

        raise Exception("Timeout reached while waiting for video upload completion.")

    def _fill_input(self, element, value):
        driver = self.driver
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        try:
            element.click()
        except Exception:
            pass
        try:
            element.clear()
        except Exception:
            pass
        try:
            element.send_keys(Keys.CONTROL, "a")
            element.send_keys(Keys.BACKSPACE)
            element.send_keys(value)
        except Exception:
            pass

        current_value = (element.get_attribute("value") or "").strip()
        if current_value == value:
            return

        driver.execute_script(
            """
            const el = arguments[0];
            const value = arguments[1];
            el.focus();
            const descriptor = Object.getOwnPropertyDescriptor(
              window.HTMLInputElement.prototype,
              "value"
            );
            if (descriptor && descriptor.set) {
              descriptor.set.call(el, value);
            } else {
              el.value = value;
            }
            el.dispatchEvent(new Event("input", { bubbles: true }));
            el.dispatchEvent(new Event("change", { bubbles: true }));
            """,
            element,
            value,
        )

        current_value = (element.get_attribute("value") or "").strip()
        if current_value != value:
            raise Exception(f"Failed to set XiaoHongShu title. Current value: {current_value!r}")

    def _fill_editor(self, element, value):
        driver = self.driver
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        try:
            element.click()
        except Exception:
            pass
        try:
            element.send_keys(Keys.CONTROL, "a")
            element.send_keys(Keys.BACKSPACE)
            element.send_keys(value)
        except Exception:
            pass

        editor_text = " ".join((element.text or "").split())
        target_text = " ".join(value.split())
        if editor_text == target_text:
            return

        driver.execute_script(
            """
            const el = arguments[0];
            const value = arguments[1];
            el.focus();
            if (window.getSelection) {
              const selection = window.getSelection();
              const range = document.createRange();
              range.selectNodeContents(el);
              selection.removeAllRanges();
              selection.addRange(range);
            }
            if (document.execCommand) {
              document.execCommand("selectAll", false, null);
              document.execCommand("insertText", false, value);
            }
            if ((el.innerText || "").trim() !== value.trim()) {
              el.innerHTML = "";
              const paragraph = document.createElement("p");
              paragraph.textContent = value;
              el.appendChild(paragraph);
            }
            el.dispatchEvent(new Event("input", { bubbles: true }));
            el.dispatchEvent(new Event("change", { bubbles: true }));
            """,
            element,
            value,
        )

        editor_text = " ".join((element.text or "").split())
        if editor_text != target_text:
            raise Exception("Failed to set XiaoHongShu description editor.")

    def wait_for_element_to_be_clickable(self, xpath, timeout=600):
        driver = self.driver
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: d.find_element(By.XPATH, xpath).is_displayed() and
                          d.find_element(By.XPATH, xpath).is_enabled() and
                          "disabled" not in d.find_element(By.XPATH, xpath).get_attribute("class") and
                          d.find_element(By.XPATH, xpath).value_of_css_property("opacity") == "1"
            )
            print(f"Element {xpath} is truly interactable.")
        except TimeoutException:
            print(f"Timed out waiting for {xpath} to become interactable.")

    def publish(self):
        if self.retry_count < 3:  # maximum 3 tries (initial + 2 retries)
            try:
                driver = self.driver
                path_mp4 = self.path_mp4
                path_cover = self.path_cover
                metadata = self.metadata
                test = self.test
                
                print("Starting the publishing process on XiaoHongShu...")
                driver.get("https://creator.xiaohongshu.com/creator/post")
                print("Navigated to post creation page.")
                
                time.sleep(1)
                dismiss_alert(driver)
                time.sleep(10)
                
                bring_to_front(["小红书", "你访问的页面不见了"])
                close_extra_tabs(driver)

                video_input = self._find_first([
                    '//input[@type="file" and contains(@accept, ".mp4")]',
                    '//div[contains(@class,"publish-page-content-media")]//input[@type="file"]',
                    '//input[@type="file"]',
                ], visible=False)
                print("Video upload field is present.")

                print(f"Uploading video from path: {path_mp4}")
                time.sleep(3)
                bring_to_front(["小红书", "你访问的页面不见了"])
                video_input.send_keys(path_mp4)
                time.sleep(3)
                self._wait_for_upload_ready(timeout=3600)
                
                print("Entering title and description.")
                title_input = self._find_first([
                    '//input[@placeholder="填写标题会有更多赞哦"]',
                    '//input[@placeholder="填写标题会有更多赞哦～"]',
                    '//div[contains(@class,"input")]//input[@type="text"]',
                    '//div[contains(@class,"title-container")]//input[@type="text"]',
                    '//*[contains(@class,"titleInput")]//input',
                ], timeout=60)
                self._fill_input(title_input, metadata['title'][:20])
                
                description_with_tags = metadata['long_description'] + " " + " ".join([f"#{tag}" for tag in metadata['tags']])
                description_editor = self._find_first([
                    '//div[contains(@class,"tiptap") and @contenteditable="true"]',
                    '//div[contains(@class,"ProseMirror") and @contenteditable="true"]',
                    '//div[contains(@class,"ql-editor") and @contenteditable="true"]',
                ], timeout=60)
                self._fill_editor(description_editor, description_with_tags[:1000])

#                 try:
#                     # print("Handling cover upload.")
#                     # cover_button_xpath = '//*[text()="编辑默认封面" or text()="修改默认封面"]'
#                     # print("Waiting 编辑默认封面...")
#                     # self.wait_for_element_to_be_clickable(cover_button_xpath)
#                     # driver.find_element(By.XPATH, cover_button_xpath).click()

                    
                
#                     # print("Waiting for the '编辑默认封面' or '修改默认封面' button...")
#                     # # The XPath checks for both possible button texts
#                     # cover_button_xpath = '//*[contains(text(),"编辑默认封面") or contains(text(),"修改默认封面")]'
#                     # # WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, cover_button_xpath)))

#                     # time.sleep(10)
                    
#                     # print("Clicking on the button...")
#                     # driver.find_element(By.XPATH, cover_button_xpath).click()

#                     # Wait for the button to not only be present but also to be clickable (enabled).
#                     print("Waiting for the '编辑默认封面' button to become clickable...")
#                     cover_button_xpath = "//button[not(@disabled) and contains(., '编辑默认封面')]"
#                     WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, cover_button_xpath)))

#                     print("Clicking on the '编辑默认封面' button...")
#                     driver.find_element(By.XPATH, cover_button_xpath).click()
#                     print("Button clicked successfully! Proceeding with further actions.")

#                     # Additional steps to upload the cover would go here
#                     # For example, finding the file input element, sending the file path, etc.
#                     # These would depend on the further HTML structure which isn't provided.

#                     print("Cover uploaded or edited successfully! Proceeding with further actions.")
                    

#                     # print("Waiting for the '编辑' button...")
#                     # edit_button_xpath = '//*[contains(@class,"btn-bottom") and contains(text(),"编辑")]'
#                     # WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, edit_button_xpath)))


#                     # print("Clicking on '编辑' button...")
#                     # driver.find_element(By.XPATH, edit_button_xpath).click()

#                     time.sleep(3)


#                     print("Waiting 上传封面")
#                     self.wait_for_element_to_be_clickable('//*[text()="上传封面"]')
#                     driver.find_element(By.XPATH, '//*[text()="上传封面"]').click()

#                     time.sleep(3)

#                     print(f"Uploading cover from path: {path_cover}")
#                     print(f"Waiting for the file input to be ready to receive the cover file path...")
#                     # file_input_xpath = '//*[@id="upload-cover-containner"]/..//input[@type="file"]'
#                     print(f"Sending cover file path to input: {path_cover}")
#                     file_input_xpath = '//input[@class="upload-input"]'
#                     time.sleep(3)
#                     driver.find_element(By.XPATH, file_input_xpath).send_keys(path_cover)
#                     time.sleep(3)
                    
#                     # driver.find_element(By.XPATH, '//*[contains(text(),"上传封面")]/../../../../..//*[text()="确定"]').click()
#                     # confirm_button_xpath = '//*[contains(text(),"确定")]'
#                     # print("Clicking '确定' to confirm upload...")
#                     # driver.find_element(By.XPATH, confirm_button_xpath).click()

#                     print("Waiting for the '确定' button to be clickable...")
#                     confirm_button_xpath = "//button[contains(@class, 'btn-confirm') and contains(., '确定')]"
#                     WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, confirm_button_xpath)))

#                     print("Clicking on the '确定' button...")
#                     driver.find_element(By.XPATH, confirm_button_xpath).click()
#                     print("Button clicked successfully! Proceeding with further actions.")
                    
#                     cover_uploaded_button_xpath = '//*[text()="修改默认封面"]'
#                     time.sleep(3)
#                     WebDriverWait(driver, 600).until(EC.presence_of_element_located((By.XPATH, cover_uploaded_button_xpath)))
#                     print("Cover uploaded successfully! Proceeding to location selection.")

#                 except Exception as e:
#                     print("Cover upload with error: ", str(e))
                

                # Location selection logic here (if applicable)

#                 def select_location(driver, location_names, retry_count=2):
#                     try:
#                         location_name = location_names[0]

#                         print(f"Attempting to select location: {location_name}")
#                         time.sleep(3)

#                         input_box = WebDriverWait(driver, 10).until(
#                             EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='请选择地点']"))
#                         )
#                         print("Location input box is clickable.")
#                         input_box.click()
#                         input_box.send_keys(location_name)
#                         input_box.send_keys(Keys.RETURN)
#                         print(f"Entered location: {location_name}")

#                         time.sleep(3)
#                         WebDriverWait(driver, 10).until(
#                             EC.visibility_of_element_located((By.CLASS_NAME, "el-autocomplete-suggestion"))
#                         )
#                         print("Dropdown suggestions are visible.")

#                         time.sleep(3)
#                         print(f"Executing JavaScript to click on the location option '{location_name}'")
#                         js_code = f"""
#                         var options = document.querySelectorAll(".el-autocomplete-suggestion__list .item .name");
#                         options.forEach(function(option) {{
#                             if (option.innerText === "香港大学") {{
#                                 option.click();
#                                 console.log("Selected option: '{location_name}'");
#                             }}
#                         }});
#                         """
#                         driver.execute_script(js_code)
#                         print(f"Location '{location_name}' selected successfully!")
#                     except TimeoutException as te:
#                         print(f"TimeoutException: {te}")
#                         if retry_count > 0 and len(location_names) > 1:
#                             print(f"Retrying to select location... Attempts left: {retry_count - 1}")
#                             select_location(driver, location_names[1:], retry_count - 1)
#                         else:
#                             print("Failed to select location after multiple attempts.")
#                     except Exception as e:
#                         print(f"Exception: {e}")
#                         traceback.print_exc()

                

#                 if self.retry_count == 0:
#                     # Try selecting the location with a list of names
#                     select_location(driver, ['The University','香港大学', 'The University of Hong Kong'])

                # Prompt the user to confirm publishing
                if test:
                    user_input = input("Do you want to publish now? Type 'yes' to confirm: ").strip().lower()
                else:
                    user_input = "yes"
                if user_input == 'yes':
                    # If user confirms, click the publish button
                    time.sleep(3)
                    publish_button = self._find_first([
                        '//div[contains(@class,"publish-page-publish-btn")]//button[.//span[normalize-space()="发布"]]',
                        '//button[.//span[normalize-space()="发布"]]',
                    ], timeout=30)
                    time.sleep(3)
                    publish_button.click()
                    
                    time.sleep(10)
                    dismiss_alert(driver)
                    time.sleep(3)

                    print("Publishing...")
                else:
                    print("Publishing cancelled by user.")

                print("Process completed successfully!")
                self.retry_count = 0  # reset retry count after successful execution
            except Exception as e:
                print(f"An error occurred: {e}")
                traceback.print_exc()
                self.retry_count += 1
                print(f"Retrying the whole process... Attempt {self.retry_count}")
                self.publish()  # Retry the whole process
        else:
            print("Maximum retry attempts reached. Process failed.")

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

        # Check if there is an existing window to work with or if a new window should be opened
    try:
        driver.current_window_handle
    except NoSuchWindowException:
        driver = webdriver.Chrome(executable_path=chrome_driver_path, options=options)


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

        # Create an instance of the XiaoHongShuPublisher
        xhs_publisher = XiaoHongShuPublisher(
            driver=driver,
            path_mp4=path_mp4,
            path_cover=path_cover,
            metadata=metadata
        )

        # Start publishing process
        xhs_publisher.publish()
