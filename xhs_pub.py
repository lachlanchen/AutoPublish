import selenium
from selenium import webdriver
import pathlib
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchWindowException, TimeoutException
import time

from utils import dismiss_alert
import traceback

class XiaoHongShuPublisher:
    def __init__(self, driver, path_mp4, path_cover, metadata):
        self.driver = driver
        self.path_mp4 = path_mp4
        self.path_cover = path_cover
        self.metadata = metadata

    # def wait_for_element_to_be_clickable(self, xpath, timeout=600):
    #     try:
    #         WebDriverWait(self.driver, timeout).until(
    #             lambda d: d.find_element(By.XPATH, xpath).is_displayed() and
    #                       d.find_element(By.XPATH, xpath).is_enabled() and
    #                       "disabled" not in d.find_element(By.XPATH, xpath).get_attribute("class") and
    #                       d.find_element(By.XPATH, xpath).value_of_css_property("opacity") == "1"
    #         )
    #         print(f"Element {xpath} is truly interactable.")
    #     except TimeoutException:
    #         print(f"Timed out waiting for {xpath} to become interactable.")

    def wait_for_element_to_be_clickable(self, xpath, timeout=600):

        time.sleep(3)

        driver = self.driver

        try:
            WebDriverWait(driver, timeout).until(
                lambda d: d.find_element(By.XPATH, xpath).is_displayed() and
                          d.find_element(By.XPATH, xpath).is_enabled() and
                          # Add checks for specific classes or attributes that indicate a disabled state
                          "disabled" not in d.find_element(By.XPATH, xpath).get_attribute("class") and
                          # Check CSS properties, e.g., ensure the element is not transparent
                          d.find_element(By.XPATH, xpath).value_of_css_property("opacity") == "1"
            )
            print(f"Element {xpath} is truly interactable.")
        except TimeoutException:
            print(f"Timed out waiting for {xpath} to become interactable.")



    def publish(self):
        driver = self.driver
        wait_for_element_to_be_clickable = self.wait_for_element_to_be_clickable
        path_mp4 = self.path_mp4
        path_cover = self.path_cover
        metadata = self.metadata

        try:
            print("Starting the publishing process on XiaoHongShu...")
            driver.get("https://creator.xiaohongshu.com/creator/post")
            time.sleep(1)
            dismiss_alert(driver)
            time.sleep(10)
            print("Navigated to post creation page.")

            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//input[@type="file"]')))
            print("Video upload field is present.")
            
            print(f"Uploading video from path: {path_mp4}")
            driver.find_element(By.XPATH, '//input[@type="file"]').send_keys(path_mp4)

            WebDriverWait(driver, 3600).until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(),"重新上传")]')))
            print("Video uploaded successfully!")

            print("Entering title and description.")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[contains(@class,"titleInput")]//input')))
            driver.find_element(By.XPATH, '//*[contains(@class,"titleInput")]//input').send_keys(metadata['title'])
            description_with_tags = metadata['long_description'] + " " + " ".join([f"#{tag}" for tag in metadata['tags']])
            driver.find_element(By.XPATH, '//*[contains(@class,"topic-container")]//p').send_keys(description_with_tags)

            print("Handling cover upload.")
            # cover_button_xpath = '//*[text()="编辑默认封面" or text()="修改默认封面"]'
            cover_button_xpath = '//*[text()="编辑默认封面" or text()="修改默认封面"]'
            time.sleep(10)
            print("Waiting 编辑默认封面...")
            wait_for_element_to_be_clickable(cover_button_xpath)
            driver.find_element(By.XPATH, cover_button_xpath).click()
            print("Waiting 上传封面")
            wait_for_element_to_be_clickable('//*[text()="上传封面"]')
            driver.find_element(By.XPATH, '//*[text()="上传封面"]').click()

            print(f"Uploading cover from path: {path_cover}")
            print(f"Waiting for the file input to be ready to receive the cover file path...")
            file_input_xpath = '//*[@id="upload-cover-containner"]/..//input[@type="file"]'
            print(f"Sending cover file path to input: {path_cover}")
            driver.find_element(By.XPATH, file_input_xpath).send_keys(path_cover)
            driver.find_element(By.XPATH, '//*[contains(text(),"上传封面")]/../../../../..//*[text()="确定"]').click()
            cover_uploaded_button_xpath = '//*[text()="修改默认封面"]'
            WebDriverWait(driver, 600).until(EC.presence_of_element_located((By.XPATH, cover_uploaded_button_xpath)))
            print("Cover uploaded successfully! Proceeding to location selection.")

            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "single-input"))).click()
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "dropdown")))
            driver.find_element(By.XPATH, ".//span[contains(text(), '香港大学')]").click()
            print("Location selected successfully!")

            # Prompt the user to confirm publishing
            # user_input = input("Do you want to publish now? Type 'yes' to confirm: ").strip().lower()
            user_input = "yes"
            if user_input == 'yes':
                # If user confirms, click the publish button
                publish_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[text()="发布"]')))
                publish_button.click()
                
                time.sleep(10)

                dismiss_alert(driver)

                print("Publishing...")
            else:
                print("Publishing cancelled by user.")

            print("Process completed successfully!")
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
    # driver = webdriver.Chrome(options=options)

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
