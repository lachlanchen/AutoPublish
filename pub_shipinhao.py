import time
import json
import traceback
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, NoAlertPresentException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import dismiss_alert, bring_to_front
from login_shipinhao import ShiPinHaoLogin
import traceback

import re

# def dismiss_alert(driver):
#     try:
#         alert = driver.switch_to.alert
#         alert.accept()
#         print("Alert was present and accepted.")
#     except NoAlertPresentException:
#         print("No alert present.")

def is_delete_button_present(driver):
    try:
        driver.find_element(By.XPATH, '//*[contains(text(), "删除")]')
        print("Delete button found, upload likely complete.")
        return True
    except NoSuchElementException:
        return False

def wait_for_element(driver, xpath, duration=30):
    return WebDriverWait(driver, duration).until(EC.presence_of_element_located((By.XPATH, xpath)))

def wait_for_element_clickable(driver, xpath, duration=30):
    return WebDriverWait(driver, duration).until(EC.element_to_be_clickable((By.XPATH, xpath)))


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
        element.clear()
        time.sleep(1)  # Wait a bit after clearing
        element.send_keys(text)

    def upload_and_confirm_cover(self):
        try:
            # Wait and click on '更换封面' if it exists
            change_cover_button = wait_for_element_clickable(self.driver, '//*[contains(text(), "更换封面")]', duration=10)
            change_cover_button.click()
            time.sleep(2)

            # Click on '上传封面' to start the cover upload
            upload_cover_button = wait_for_element_clickable(self.driver, '//*[contains(text(), "上传封面")]', duration=10)
            upload_cover_button.click()
            time.sleep(2)

            # Interact with the file input to upload the cover file
            file_input_xpath = '//input[@type="file" and @accept="image/jpeg,image/jpg,image/png"]'
            file_input = wait_for_element(self.driver, file_input_xpath, duration=10)
            file_input.send_keys(self.thumbnail_path)
            time.sleep(2)

            # Confirm the upload by clicking on '确认'
            confirm_button_xpath = '//*[contains(@class, "finder-dialog-footer")]//*[contains(text(), "确认")]'
            confirm_button = wait_for_element_clickable(self.driver, confirm_button_xpath, duration=10)
            confirm_button.click()
            time.sleep(2)

        except Exception as e:
            print(f"An error occurred during cover upload: {e}")
            # Close the dialog if there's an error
            try:
                close_button = wait_for_element_clickable(self.driver, '//button[contains(@class, "weui-desktop-dialog__close-btn")]', duration=10)
                close_button.click()
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
            ("香港大学", "香港大学"),
            ("香港特别行政区", "香港特别行政区"),
            (None, "不显示位置")  # Use None to indicate no typing is required
        ]
        
        for location_input_text, _ in location_options:
            try:
                if location_input_text:
                    # Click on the position display wrapper
                    position_display_wrap = wait_for_element(driver, '//*[@class="position-display-wrap"]', 30)
                    position_display_wrap.click()
                    time.sleep(3)

                    # Enter location in the search box
                    location_input = wait_for_element(driver, '//input[@placeholder="搜索附近位置"]', 30)
                    self.clear_and_type(location_input, location_input_text)
                    time.sleep(3)

                    # Click the search button if needed
                    search_button = wait_for_element(driver, '//button[contains(@class, "weui-desktop-icon-btn weui-desktop-search__btn")]', 30)
                    search_button.click()
                    time.sleep(3)

                for _, location_click_text in location_options:
                    try:
                        # Try clicking on the specified location
                        location_option = wait_for_element_clickable(driver, f"//div[contains(@class, 'location-item-info')]//div[text()='{location_click_text}']", 30)
                        location_option.click()
                        time.sleep(3)
                        print(f"Clicked on location: {location_click_text}")
                        break  # Break the loop if click was successful
                    except Exception as e:
                        print(f"Could not click on location: {location_click_text}. Error: {e}")
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
                driver.get("https://channels.weixin.qq.com/post/create")
                dismiss_alert(driver)
                time.sleep(10)

                bring_to_front(["视频号"])

                wait_for_element(driver, "//span[contains(text(), '发表动态')]", 30)
                dismiss_alert(driver)
                time.sleep(3)

                # Upload video
                video_upload_input = wait_for_element(driver, '//input[@type="file"]', 30)
                video_upload_input.send_keys(video_path)
                print("Video uploading...")

                start_time = time.time()
                timeout = 3600  # 3600 seconds timeout
                while not is_delete_button_present(driver):
                    if time.time() - start_time > timeout:
                        raise Exception("Timeout reached while waiting for video to be uploaded or for the delete button to appear.")
                    print("Waiting for the video to upload or for the delete button to appear...")
                    dismiss_alert(driver)
                    time.sleep(5)

                time.sleep(10)  # Wait for 10 seconds after detecting the delete button
                print("Video uploaded or delete button detected!")

                # Upload and confirm cover
                self.upload_and_confirm_cover()
                time.sleep(3)

                # Set description
                video_description_with_tags = self.metadata["long_description"] + " " + " ".join("#" + tag for tag in self.metadata["tags"])
                description_input = wait_for_element(driver, '//*[@data-placeholder="添加描述"]', 30)
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

                self.set_location(driver)

                # Set playlist
                collection_dropdown = wait_for_element_clickable(driver, "//div[@class='post-album-display-wrap']//div[@class='display-text' and contains(text(), '选择合集')]", 30)
                collection_dropdown.click()
                time.sleep(3)

                simple_life_collection = wait_for_element_clickable(driver, "//div[@class='common-option-list-wrap option-list-wrap']//div[@class='item']//div[@class='name' and text()='简单生活']", 30)
                simple_life_collection.click()
                time.sleep(3)

                # Set short title
                title = metadata['title'] if 6 <= len(metadata['title']) <= 16 else metadata['brief_description'][:16]
                short_title_input = driver.find_element(By.XPATH, '//input[@placeholder="概括视频主要内容，字数建议6-16个字符"]')
                self.clear_and_type(short_title_input, self.clean_title(title[:16]))
                time.sleep(3)

                # Original declaration
                original_content_checkbox = driver.find_element(By.XPATH, '//input[@class="ant-checkbox-input" and @type="checkbox"]')
                original_content_checkbox.click()
                time.sleep(3)

                # Define the dropdown and select "生活"
                dropdown_label = driver.find_element(By.XPATH, '//div[@class="weui-desktop-form__dropdown weui-desktop-form__dropdown__default"]/dl')
                dropdown_label.click()
                time.sleep(3)

                life_option = driver.find_element(By.XPATH, '//span[@class="weui-desktop-dropdown__list-ele__text" and text()="生活"]')
                life_option.click()
                time.sleep(3)

                # Check the agreement checkbox
                agreement_checkbox = driver.find_element(By.XPATH, '//div[@class="original-proto-wrapper"]//input[@type="checkbox"]')
                if not agreement_checkbox.is_selected():
                    agreement_checkbox.click()
                    time.sleep(3)

                # Click on the "声明原创" button once it's clickable
                declare_original_button = wait_for_element_clickable(driver, '//div[@class="weui-desktop-dialog__ft"]//button[contains(text(), "声明原创")]', 30)
                declare_original_button.click()
                time.sleep(3)

                # Click publish button
                if test:
                    user_input = input("Do you want to publish now? Type 'yes' to confirm: ").strip().lower()
                else:
                    user_input = "yes"
                if user_input == 'yes':
                    submit_button = wait_for_element(driver, '//*[text()="发表"]', 30)
                    submit_button.click()
                    time.sleep(10)
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
