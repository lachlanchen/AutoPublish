import pathlib
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, NoSuchWindowException, TimeoutException
import time

from utils import dismiss_alert

import traceback

class BilibiliPublisher:
    def __init__(self, driver, path_mp4, path_cover, metadata):
        self.driver = driver
        self.path_mp4 = path_mp4
        self.path_cover = path_cover
        self.metadata = metadata

    def wait_for_element_to_be_clickable(self, xpath, timeout=600):
        time.sleep(3)
        # try:
        #     WebDriverWait(self.driver, timeout).until(
        #         EC.element_to_be_clickable((By.XPATH, xpath))
        #     )
        #     print(f"Element {xpath} is clickable.")
        # except TimeoutException:
        #     print(f"Timed out waiting for {xpath} to become clickable.")

    def publish(self):
        driver = self.driver
        wait_for_element_to_be_clickable = self.wait_for_element_to_be_clickable
        path_mp4 = self.path_mp4
        path_cover = self.path_cover
        metadata = self.metadata

        try:
            print("Starting the publishing process on Bilibili...")
            driver.get("https://member.bilibili.com/platform/upload/video/frame")
            time.sleep(1)
            dismiss_alert(driver)
            time.sleep(10)
            
            print(f"Uploading video from path: {path_mp4}")
            upload_input_xpath = '//input[@type="file" and contains(@accept,"mp4")]'
            wait_for_element_to_be_clickable(upload_input_xpath)
            driver.find_element(By.XPATH, upload_input_xpath).send_keys(path_mp4)

            print("Waiting for the video to be uploaded...")
            WebDriverWait(driver, 3600).until(EC.presence_of_element_located((By.XPATH, '//*[text()="上传完成"]')))
            print("Video uploaded successfully!")

            print("Handling cover upload.")
            # Click on the '更改封面' button to start the cover upload process
            edit_cover_button_xpath = '//*[text()="更改封面"]'
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, edit_cover_button_xpath))).click()
            # Wait for the '上传封面' option to become clickable and click it
            upload_cover_option_xpath = '//*[text()="上传封面"]'
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, upload_cover_option_xpath))).click()
            file_input_xpath = "//input[@type='file' and @accept='image/png, image/jpeg']"
            file_input_element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, file_input_xpath)))
            # Send the file path to the hidden file input element
            file_input_element.send_keys(path_cover)
            time.sleep(3)
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
            result = driver.execute_script(js_code)
            # Print the result of the JavaScript execution
            print(result)
            time.sleep(3)        
            print("Cover upload finished.")

            # Enter Title
            print("Entering title...")
            title_input_xpath = '//input[contains(@placeholder,"请输入稿件标题")]'
            wait_for_element_to_be_clickable(title_input_xpath)
            driver.find_element(By.XPATH, title_input_xpath).clear()
            driver.find_element(By.XPATH, title_input_xpath).send_keys(metadata['title'])

            # Enter Description
            print("Entering description...")
            description_with_tags = metadata['brief_description'] + " " + " ".join([f"#{tag}" for tag in metadata['tags']])
            desc_input_xpath = '//*[@editor_id="desc_at_editor"]//br'
            wait_for_element_to_be_clickable(desc_input_xpath)
            driver.find_element(By.XPATH, desc_input_xpath).send_keys(description_with_tags)

            # Select Category
            print("Selecting category...")
            category_select_xpath = '//*[contains(@class,"select-item-cont")]'
            wait_for_element_to_be_clickable(category_select_xpath)
            driver.find_element(By.XPATH, category_select_xpath).click()
            driver.find_element(By.XPATH, '//*[text()="推荐选择"]').click()
            driver.find_element(By.XPATH, '//*[text()="日常"]').click()

            # Add Tags
            print("Adding tags...")
            tag_input_xpath = '//input[@placeholder="按回车键Enter创建标签"]'
            for tag in metadata['tags']:
                wait_for_element_to_be_clickable(tag_input_xpath)
                driver.find_element(By.XPATH, tag_input_xpath).send_keys(tag)
                driver.find_element(By.XPATH, tag_input_xpath).send_keys(Keys.ENTER)
                time.sleep(0.1)

            # Prompt for Publishing
            # user_input = input("Do you want to publish now? Type 'yes' to confirm: ").strip().lower()
            user_input = "yes"
            if user_input == 'yes':
                # Click Publish
                print("Publishing the video...")
                publish_button_xpath = '//*[text()="立即投稿"]'
                wait_for_element_to_be_clickable(publish_button_xpath)
                driver.find_element(By.XPATH, publish_button_xpath).click()
                
                time.sleep(10)

                dismiss_alert(driver)
                print("Video published successfully!")
            else:
                print("Publishing cancelled by the user.")

        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()

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
            "description": "跟随我们的味蕾之旅，发现为何这款烤鸡让人赞不绝口！",
            "tags": ["美食", "烤鸡", "推荐"]
        }

        # Create an instance of the BilibiliPublisher
        bilibili_publisher = BilibiliPublisher(
            driver=driver,
            path_mp4=path_mp4,
            path_cover=path_cover,
            metadata=metadata
        )

        # Start publishing process
        bilibili_publisher.publish()
