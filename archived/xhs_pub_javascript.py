import selenium
from selenium import webdriver
import pathlib
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchWindowException, TimeoutException, JavascriptException
import time

from utils import dismiss_alert
import traceback
import json
import pathlib

class XiaoHongShuPublisher:
    def __init__(self, driver, path_mp4, path_cover, metadata, test=False):
        self.driver = driver
        self.path_mp4 = path_mp4
        self.path_cover = path_cover
        self.metadata = metadata
        self.test = test

    def execute_script(self, script, *args):
        try:
            return self.driver.execute_script(script, *args)
        except JavascriptException as e:
            print(f"JavaScript error: {e}")
            traceback.print_exc()

    def wait_for_element_to_be_clickable(self, xpath, timeout=600):
        wait_script = """
            var xpath = arguments[0];
            var callback = arguments[arguments.length - 1];
            var checkVisibility = function() {
                var element = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                if (element && element.offsetHeight > 0 && element.offsetWidth > 0 && !element.disabled && getComputedStyle(element).opacity != '0') {
                    callback(true);
                } else {
                    callback(false);
                }
            };
            setTimeout(checkVisibility, 3000);
        """
        time.sleep(3)  # Sleep for stability
        WebDriverWait(self.driver, timeout).until(
            lambda d: self.execute_script(wait_script, xpath) is True
        )
        print(f"Element {xpath} is truly interactable.")

    def publish(self):
        driver = self.driver
        wait_for_element_to_be_clickable = self.wait_for_element_to_be_clickable
        path_mp4 = self.path_mp4
        path_cover = self.path_cover
        metadata = self.metadata
        test = self.test

        try:
            print("Starting the publishing process on XiaoHongShu...")
            driver.get("https://creator.xiaohongshu.com/creator/post")
            time.sleep(1)
            dismiss_alert(driver)
            time.sleep(10)
            print("Navigated to post creation page.")
            
            # Wait for the video upload field to be present
            video_upload_field_xpath = '.video-uploader-container .upload-input'
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, video_upload_field_xpath))
            )
            print("Video upload field is present.")

            # Uploading video using Selenium's send_keys
            video_upload_element = driver.find_element(By.CSS_SELECTOR, video_upload_field_xpath)
            video_upload_element.send_keys(path_mp4)
            print(f"Uploading video from path: {path_mp4}")

            # Wait for the video to be uploaded
            WebDriverWait(driver, 3600).until(
                EC.presence_of_element_located((By.XPATH, '//*[contains(text(),"重新上传")]'))
            )
            print("Video uploaded successfully!")

            time.sleep(3)

            
            # Entering title and description
            input_metadata_script = """
                var title = arguments[0];
                var description = arguments[1];
                var tags = arguments[2]; // Assuming tags is an array of strings

                var titleInput = document.querySelector('.titleInput input');
                var descriptionInput = document.querySelector('#post-textarea');

                if (titleInput) {
                    titleInput.value = title;
                }

                if (descriptionInput) {
                    descriptionInput.innerText = description + " " + tags.map(tag => '#' + tag).join(' ');
                }
            """
            self.execute_script(input_metadata_script, metadata['title'], metadata['long_description'], metadata['tags'])
            print("Title and description entered successfully!")


            time.sleep(5)

            
            # Handling cover upload
            # JavaScript code to click the correct button
            cover_button_script = """
                var editButton = document.evaluate('//button[text()="编辑默认封面"]', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                var modifyButton = document.evaluate('//button[text()="修改默认封面"]', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                
                var buttonToClick = editButton || modifyButton;
                if (buttonToClick && buttonToClick.click) {
                    buttonToClick.click();
                }
            """
            self.execute_script(cover_button_script)
            time.sleep(3)  # Wait for the dialog to open


            # Click on '上传封面' using JavaScript
            upload_cover_button_script = """
                var uploadButton = document.querySelector('//*[text()="上传封面"]');
                if (uploadButton) {
                    uploadButton.click();
                }
            """
            self.execute_script(upload_cover_button_script)
            time.sleep(3)  # Wait for the file input to become accessible

            # Selenium code to send the file path to the input
            file_input = driver.find_element(By.CSS_SELECTOR, ".upload-input[type='file']")
            file_input.send_keys(path_cover)
            time.sleep(3)  # Wait for the upload to complete

            # JavaScript code to click the '完成' button
            complete_button_script = """
                var completeButton = document.querySelector('//*[text()="完成"]');
                if (completeButton) {
                    completeButton.click();
                }
            """
            self.execute_script(complete_button_script)
            time.sleep(3)  # Wait for the action to complete



            # Checking if the cover has been uploaded
            WebDriverWait(driver, 600).until(
                EC.presence_of_element_located((By.XPATH, '//*[text()="修改默认封面"]'))
            )
            print("Cover uploaded successfully! Proceeding to location selection.")

            # Location selection
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "single-input"))).click()
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "dropdown")))
            select_location_script = """
                var location = '香港大学';
                var locationElement = document.querySelector(".//span[contains(text(), '" + location + "')]");
                if (locationElement) {
                    locationElement.click();
                }
            """
            self.execute_script(select_location_script)
            print("Location selected successfully!")

            # Prompt the user to confirm publishing
            if test:
                user_input = input("Do you want to publish now? Type 'yes' to confirm: ").strip().lower()
            else:
                user_input = "yes"
            if user_input == 'yes':
                # If user confirms, click the publish button
                publish_script = """
                    var publishButton = document.evaluate('//*[text()="发布"]', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    if (publishButton) {
                        publishButton.click();
                    }
                """
                self.execute_script(publish_script)
                time.sleep(10)  # Wait for the publish action to complete

                dismiss_alert(driver)

                print("Publishing...")
            else:
                print("Publishing cancelled by user.")

            print("Process completed successfully!")
        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()



def get_media_info(catalog):
    path = pathlib.Path(catalog)
    path_mp4 = next((str(p) for p in path.glob('*.mp4')), None)
    path_cover = next((str(p) for p in path.glob('*') if p.suffix in ['.png', '.jpg']), None)
    path_metadata = next((str(p) for p in path.glob('*.json')), None)
    
    metadata = None
    if path_metadata:
        with open(path_metadata, 'r') as f:
            metadata = json.load(f)
    
    return path_mp4, path_cover, metadata

if __name__ == "__main__":
    # Constants
    catalog_mp4 = r"/Users/lachlan/Nutstore Files/Vlog/transcription_data/IMG_5304"
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

    # Get the video, cover paths, and metadata
    path_mp4, path_cover, metadata = get_media_info(catalog_mp4)
    if not path_mp4 or not path_cover or not metadata:
        print("Video, cover file, or metadata not found. Exiting...")
    else:
        print(f"Found video path: {path_mp4}")
        print(f"Found cover path: {path_cover}")
        print(f"Loaded metadata: {metadata}")

        # Create an instance of the XiaoHongShuPublisher
        pub_xhslisher = XiaoHongShuPublisher(
            driver=driver,
            path_mp4=path_mp4,
            path_cover=path_cover,
            metadata=metadata,
            test=True
        )

        # Start publishing process
        pub_xhslisher.publish()

