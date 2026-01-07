import time
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.common.exceptions import NoAlertPresentException
import traceback

from utils import dismiss_alert, bring_to_front
# from utils import dismiss_alert, bring_to_front
#   This assumes you have a 'utils.py' containing these functions. 
#   If not, just define them in this file as needed:
# def dismiss_alert(driver, dismiss=False):
#     try:
#         alert = driver.switch_to.alert
#         if dismiss:
#             alert.dismiss()
#         else:
#             alert.accept()  # Use alert.accept() if you want to accept the alert.
#         print("Alert was present and dismissed.")
#     except NoAlertPresentException:
#         print("No alert present.")

# def bring_to_front(window_titles):
#     # This function might use OS-specific methods to bring certain windows to front.
#     pass

class YouTubePublishingException(Exception):
    """Base class for exceptions in this module."""
    pass

class DailyUploadLimitReachedException(YouTubePublishingException):
    """Exception raised when the daily upload limit is reached."""
    def __init__(self, message="Daily upload limit reached."):
        self.message = message
        super().__init__(self.message)

class ProcessingTimeoutException(YouTubePublishingException):
    """Exception raised when processing time exceeds the limit."""
    def __init__(self, message="Processing time exceeded the limit."):
        self.message = message
        super().__init__(self.message)

class VideoPublishingException(YouTubePublishingException):
    """Exception raised for errors during video publishing."""
    def __init__(self, message="An error occurred during video publishing."):
        self.message = message
        super().__init__(self.message)

def remove_non_bmp(text):
    """
    Strips out any characters outside the Basic Multilingual Plane (BMP),
    since ChromeDriver may fail on such characters.
    """
    return ''.join(ch for ch in text if ord(ch) <= 0xFFFF)

class YouTubePublisher:
    def __init__(self, driver, video_path, thumbnail_path, metadata, test=False):
        self.driver = driver
        self.video_path = video_path
        self.thumbnail_path = thumbnail_path
        self.metadata = metadata
        self.test = test
        # self.load_metadata()
        
    # def load_metadata(self):
    #     """
    #     Sample method if you'd prefer loading the metadata from a JSON file instead
    #     of passing it directly to the constructor.
    #     """
    #     try:
    #         with open(self.metadata_path, 'r') as file:
    #             self.metadata = json.load(file)
    #         print('Metadata loaded successfully.')
    #     except Exception as e:
    #         print(f"An error occurred while loading the metadata: {e}")
    #         self.metadata = {}
    
    def upload_video(self):
        """
        Navigates to the YouTube upload page and attaches the video file.
        """
        try:
            self.driver.get('https://www.youtube.com/upload')
            time.sleep(1)  # Wait for the page to load
            
            dismiss_alert(self.driver)
            
            time.sleep(10)  # Wait a bit longer for upload page elements

            bring_to_front(["YouTube"])
            
            # Upload the video file
            absolute_video_path = str(Path.cwd() / self.video_path)
            self.driver.find_element(By.XPATH, "//input[@type='file']").send_keys(absolute_video_path)
            print('Attached video {}'.format(self.video_path))
        except Exception as e:
            raise Exception(f"Failed to upload video: {e}")
    
    # def wait_for_processing(self):
    #     """
    #     Alternative simpler method to wait for a specific text to appear.
    #     """
    #     try:
    #         expected_text = "Checks complete. No issues found."
    #         wait = WebDriverWait(self.driver, 1200)  # Adjust timeout as needed
    #         span_xpath = f"//span[contains(@class, 'progress-label') and contains(@class, 'style-scope') and contains(@class, 'ytcp-video-upload-progress') and contains(text(), '{expected_text}')]"
    #         wait.until(EC.presence_of_element_located((By.XPATH, span_xpath)))
    #         print('The expected text is present in the span element.')
    #     except TimeoutException:
    #         raise Exception("Processing time exceeded the limit.")

    # def wait_for_processing(self, mode="", interval=5, duration=600):
    #     """
    #     Another possible approach to watch for expected texts or errors.
    #     """
    #     try:
    #         if mode == "check":
    #             expected_text = "Checks complete. No issues found."
    #         elif mode == "upload":
    #             expected_text = "Upload complete"
    #             expected_text_spare = "Processing up to"
    #         else:
    #             expected_text = "complete"

    #         error_text = "Daily upload limit reached"
    #         wait = WebDriverWait(self.driver, 600)  # Adjust timeout as needed

    #         # Check for the presence of either the expected text or the error message
    #         span_xpath = f"//span[contains(@class, 'progress-label') and contains(@class, 'style-scope') and contains(@class, 'ytcp-video-upload-progress') and contains(text(), '{expected_text}')]"
    #         error_xpath = f"//div[contains(@class, 'error-short') and contains(@class, 'style-scope') and contains(text(), '{error_text}')]"

    #         while True:
    #             if self.driver.find_elements(By.XPATH, span_xpath):
    #                 print('The expected text is present in the span element.')
    #                 break
    #             elif self.driver.find_elements(By.XPATH, error_xpath):
    #                 raise DailyUploadLimitReachedException("Daily upload limit reached.")
    #             else:
    #                 time.sleep(interval)  # Wait for a while before checking again
    #     except TimeoutException:
    #         raise ProcessingTimeoutException()

    def wait_for_processing(self, mode="", interval=5, duration=600):
        """
        Waits until the video finishes uploading or checking,
        or an error/daily limit is encountered.
        """
        try:
            expected_texts = []
            if mode == "check":
                expected_texts.append("Checks complete. No issues found.")
            elif mode == "upload":
                expected_texts.extend(["Upload complete", "Processing up to", "Checking", "Checks complete. No issues found."])
            else:
                expected_texts.extend(["complete", "Complete", "Processing up to", "Checking", "Checks complete. No issues found."])

            error_text = "Daily upload limit reached"
            wait = WebDriverWait(self.driver, duration)  # Adjust total timeout as needed

            error_xpath = "//div[contains(@class, 'error-short') and contains(@class, 'style-scope') and contains(text(), '{}')]".format(error_text)

            start_time = time.time()
            while True:
                current_time = time.time()
                if current_time - start_time > duration:
                    raise TimeoutException()

                found = False
                for expected_text in expected_texts:
                    span_xpath = "//span[contains(@class, 'progress-label') and contains(@class, 'style-scope') and contains(@class, 'ytcp-video-upload-progress') and contains(text(), '{}')]".format(expected_text)
                    if self.driver.find_elements(By.XPATH, span_xpath):
                        print('The expected text "{}" is present in the span element.'.format(expected_text))
                        found = True
                        break

                if found:
                    break
                elif self.driver.find_elements(By.XPATH, error_xpath):
                    raise DailyUploadLimitReachedException("Daily upload limit reached.")
                else:
                    time.sleep(interval)  # Wait for a while before checking again
        except TimeoutException:
            raise ProcessingTimeoutException()

    def create_video_title_with_limited_tags(self, metadata):
        """
        Creates a video title that includes as many tags as possible without exceeding
        the 100-character limit. Also ensures we stay within the BMP for ChromeDriver.
        """
        max_length = 100  # Maximum length of the title with tags
        title = metadata["title"]
        tags = metadata["tags"]
        
        # Start with the full title, then truncate if necessary
        if len(title) > max_length:
            # If the title itself exceeds the max length, truncate it
            optimized_title = title[:max_length]
        else:
            optimized_title = title
            remaining_length = max_length - len(optimized_title) - 1  # Space for separator
        
            # Try to add as many tags as possible
            tags_str = ""
            for tag in tags:
                tag_with_prefix = " #" + tag.replace(" ", "")
                if len(tag_with_prefix) <= remaining_length:
                    tags_str += tag_with_prefix
                    remaining_length -= len(tag_with_prefix)
                else:
                    # No more tags can be added without exceeding the max length
                    break
            
            # Append tags to the title if there's any space left
            if tags_str:
                optimized_title += " " + tags_str.strip()
        
        # Strip out non-BMP characters from the final title string
        optimized_title = remove_non_bmp(optimized_title)
        return optimized_title

    def set_video_details(self):
        """
        Sets the title and description of the uploaded video.
        Ensures that both fields are stripped of non-BMP characters.
        """
        try:
            # Prepare title
            video_title_with_tags = self.create_video_title_with_limited_tags(self.metadata)
            
            # Prepare description
            # Strip out non-BMP characters from the description to avoid ChromeDriver error
            safe_description = remove_non_bmp(self.metadata["long_description"])

            title_input_xpath = "//div[@id='textbox'][@contenteditable='true']"
            title_input = WebDriverWait(self.driver, 600).until(EC.element_to_be_clickable((By.XPATH, title_input_xpath)))
            title_input.clear()
            title_input.send_keys(video_title_with_tags)
            print(f'The video title was set to "{video_title_with_tags}"')

            time.sleep(3)
            
            description_input_xpath = "//div[@id='textbox'][@contenteditable='true' and @aria-label='Tell viewers about your video (type @ to mention a channel)']"
            description_input = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, description_input_xpath)))
            description_input.clear()
            description_input.send_keys(safe_description)
            print(f'The video description was set to "{self.metadata["long_description"]}" (non-BMP chars removed if any)')
        except Exception as e:
            raise Exception(f"Failed to set video details: {e}")
    
    def set_thumbnail(self):
        """
        Sets the thumbnail for the video if the element is present.
        """
        try:
            absolute_thumbnail_path = str(Path.cwd() / self.thumbnail_path)
            self.driver.find_element(By.XPATH, "//input[@id='file-loader']").send_keys(absolute_thumbnail_path)
            print('Attached thumbnail {}'.format(self.thumbnail_path))
        except NoSuchElementException:
            print('Thumbnail upload option not available.')
        except Exception as e:
            raise Exception(f"Failed to set thumbnail: {e}")
            
    def set_playlist(self):
        """
        Clicks and selects a playlist if available. 
        Adjust the playlist name as needed.
        """
        playlist_name = "SimpleLife"
        try:
            dropdown_trigger = self.driver.find_element(By.CSS_SELECTOR, "ytcp-text-dropdown-trigger.dropdown")
            dropdown_trigger.click()
            print('Clicked on playlist dropdown')

            wait = WebDriverWait(self.driver, 10)
            option_xpath = f"//span[contains(@class, 'style-scope') and text()='{playlist_name}']"
            playlist_option = wait.until(EC.visibility_of_element_located((By.XPATH, option_xpath)))
            playlist_option.click()
            print(f'Selected playlist: {playlist_name}')
            
            wait = WebDriverWait(self.driver, 10)  # Adjust timeout as needed
            done_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "ytcp-button.done-button")))
            done_button.click()
            print('Clicked on the Done button.')

        except Exception as e:
            print(f"An error occurred during playlist selection: {e}")
            
    def set_not_for_kids(self):
        """
        Clicks the 'Not Made for Kids' button to ensure no audience restrictions.
        """
        try:
            wait = WebDriverWait(self.driver, 10)  # Adjust timeout as needed
            not_made_for_kids_button = wait.until(EC.element_to_be_clickable((By.NAME, "VIDEO_MADE_FOR_KIDS_NOT_MFK")))
            not_made_for_kids_button.click()
            print('Clicked on the Not Made for Kids button.')
        except Exception as e:
            print(f"An error occurred when trying to click on the Not Made for Kids button: {e}")
            raise Exception(f"Failed to set Not Made for Kids: {e}")

    def set_tags_and_more(self):
        """
        Clicks 'Show more' and adds tags. 
        Also ensures the tags are within BMP if necessary (usually short ASCII tags won't cause issues).
        """
        try:
            show_more_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "toggle-button")))
            show_more_button.click()
            print('Clicked on the Show more button.')
            
            tags = self.metadata["tags"]
            tags_string = ', '.join(tags) + ','
            # If you need to remove non-BMP from tags, do something like:
            # tags_string = remove_non_bmp(', '.join(tags)) + ','

            tags_input_xpath = "//input[@id='text-input' and @class='text-input style-scope ytcp-chip-bar' and @aria-label='Tags']"
            tags_input = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, tags_input_xpath)))
            tags_input.send_keys(tags_string)
            print(f'Tags entered: {tags_string}')
        except TimeoutException:
            raise Exception("Failed to click on the Show more button or set tags.")
    
    def set_visibility_and_publish(self):
        """
        Clicks 'Next' a few times, sets the video to PUBLIC, and finally clicks Publish.
        """
        try:
            for _ in range(3):
                next_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "next-button")))
                next_button.click()
                time.sleep(2)
            
            # Set the video's visibility and publish
            self.driver.find_element(By.NAME, 'PUBLIC').click()
            time.sleep(3)
            
            if self.test:
                user_input = input("Do you want to publish now? Type 'yes' to confirm: ").strip().lower()
                if user_input != 'yes':
                    print("Publishing cancelled by user.")
                    return

            publish_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "done-button")))
            publish_button.click()
            print('Clicked on the Publish button.')
            time.sleep(3)

            # Retrieve video ID (This assumes you are on the video's page or at least
            # it might reflect the video ID in the URL, which can vary)
            video_id = self.driver.current_url.split('/')[-1]
            print(f'Video ID: {video_id}')
        except TimeoutException:
            raise Exception("Failed to set visibility or click on the Publish button.")
    
    def publish(self):
        """
        Main method to orchestrate the entire publishing process, 
        including retry logic for certain errors.
        """
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                self.upload_video()
                    
                # Wait for the upload process to complete
                self.wait_for_processing(mode="upload", interval=0.5, duration=1800)

                self.set_video_details()
                time.sleep(3)
                self.set_thumbnail()
                time.sleep(3)
                self.set_playlist()
                time.sleep(3)
                self.set_not_for_kids()
                time.sleep(3)
                self.set_tags_and_more()
                time.sleep(3)
                    
                # Wait for the final checks to finish before clicking Publish
                self.wait_for_processing(mode="check", interval=1, duration=600)

                self.set_visibility_and_publish()

                time.sleep(10)
                print("Video published successfully.")
                break  # Break out of the loop if publish is successful

            except DailyUploadLimitReachedException as e:
                print(f"Publishing failed: {e.message}")
                break
            except Exception as e:
                print(f"Attempt {attempt + 1} of {max_attempts} failed: {e}")
                if attempt < max_attempts - 1:
                    print("Retrying...")
                    time.sleep(5)  # Wait before retrying
                else:
                    print("Maximum attempts reached. Publishing failed.")
                    # raise  # Optionally, re-raise the last exception


if __name__ == "__main__":
    # Sample usage code
    chrome_debugging_port = "9222"
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{chrome_debugging_port}")
    driver = webdriver.Chrome(options=chrome_options)

    video_path = "videos/IMG_5303/IMG_5303_highlighted.mp4"
    thumbnail_path = "videos/IMG_5303/IMG_5303_cover.jpg"

    # If your metadata is actually a JSON file path, you could load it.
    # For this example, we assume it's a dict with the necessary fields.
    # Or you can pass the path to YouTubePublisher and call load_metadata().
    metadata_file_path = "videos/IMG_5303/IMG_5303_metadata.json"
    # Sample content of metadata might be:
    # {
    #   "title": "电吉他的魅力探索",
    #   "long_description": "这段视频里介绍电吉他的迷人之处 🎸",
    #   "tags": ["吉他", "音乐", "演奏"]
    # }

    # For demonstration, let's pretend we read the JSON:
    with open(metadata_file_path, 'r', encoding='utf-8') as mf:
        metadata = json.load(mf)
    
    test_mode = True  # Set to False to disable test mode

    yt_publisher = YouTubePublisher(driver, video_path, thumbnail_path, metadata, test_mode)
    
    max_attempts = 1
    for attempt in range(max_attempts):
        try:
            yt_publisher.publish()
            break
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_attempts - 1:
                print("Maximum attempts reached. Publishing failed.")
            else:
                print("Retrying...")
                time.sleep(5)  # Wait before retrying
    
    # driver.quit()
