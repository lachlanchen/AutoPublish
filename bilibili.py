import selenium
from selenium import webdriver
import pathlib
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, NoSuchWindowException, TimeoutException
from selenium.webdriver.common.keys import Keys



from utils import dismiss_alert

# Constants
catalog_mp4 = r"/Users/lachlan/Documents/iProjects/auto-publish/videos"
describe = "跑步 #搞笑 #电影 #视觉震撼"

# Initialize Chrome options
options = webdriver.ChromeOptions()
options.add_experimental_option("debuggerAddress", "127.0.0.1:5003")
driver = webdriver.Chrome(options=options)

# Function to get the video and cover paths
def get_media_paths(catalog):
    path = pathlib.Path(catalog)
    path_mp4 = next((str(p) for p in path.glob('*.mp4')), None)
    path_cover = next((str(p) for p in path.glob('*') if p.suffix in ['.png', '.jpg']), None)
    return path_mp4, path_cover

# Function to wait until the element is truly interactable
def wait_for_element_to_be_clickable(driver, xpath, timeout=600):

    time.sleep(3)
    # try:
    #     WebDriverWait(driver, timeout).until(
    #         lambda d: d.find_element(By.XPATH, xpath).is_displayed() and
    #                   d.find_element(By.XPATH, xpath).is_enabled()
    #     )
    #     print(f"Element {xpath} is truly interactable.")
    # except TimeoutException:
    #     print(f"Timed out waiting for {xpath} to become interactable.")


# Function to scroll an element into view and then click it
def scroll_and_click(driver, xpath):
    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
    driver.execute_script("arguments[0].scrollIntoView(true);", element)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()

# Function to select a category and subcategory
def select_category(driver, category_name, subcategory_name):
    try:
        print(f"Selecting category: {category_name} > {subcategory_name}...")
        category_select_xpath = '//*[contains(@class,"select-item-cont")]'
        category_option_xpath = f'//*[text()="{category_name}"]'
        subcategory_option_xpath = f'//*[text()="{subcategory_name}"]'

        scroll_and_click(driver, category_select_xpath)  # Click to open the category dropdown
        scroll_and_click(driver, category_option_xpath)  # Select the main category
        scroll_and_click(driver, subcategory_option_xpath)  # Select the subcategory

        print(f"Category '{category_name} > {subcategory_name}' selected successfully!")
    except Exception as e:
        print(f"An error occurred while selecting the category: {e}")


# Function to publish video on Bilibili
def publish_bilibili(path_mp4, path_cover):
    try:
        print("Starting the publishing process on Bilibili...")
        driver.get("https://member.bilibili.com/platform/upload/video/frame")
        dismiss_alert(driver)
        time.sleep(3)
        
        print(f"Uploading video from path: {path_mp4}")
        upload_input_xpath = '//input[@type="file" and contains(@accept,"mp4")]'
        wait_for_element_to_be_clickable(driver, upload_input_xpath)
        driver.find_element(By.XPATH, upload_input_xpath).send_keys(path_mp4)

        print("Waiting for the video to be uploaded...")
        WebDriverWait(driver, 600).until(EC.presence_of_element_located((By.XPATH, '//*[text()="上传完成"]')))
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
        title_input_xpath = '//input[contains(@placeholder,"标题")]'
        wait_for_element_to_be_clickable(driver, title_input_xpath)
        driver.find_element(By.XPATH, title_input_xpath).clear()
        driver.find_element(By.XPATH, title_input_xpath).send_keys(describe[:describe.index(" #")])

        # Enter Description
        print("Entering description...")
        desc_input_xpath = '//*[@editor_id="desc_at_editor"]//br'
        wait_for_element_to_be_clickable(driver, desc_input_xpath)
        driver.find_element(By.XPATH, desc_input_xpath).send_keys(describe)

        # Select Category
        print("Selecting category...")
        category_select_xpath = '//*[contains(@class,"select-item-cont")]'
        wait_for_element_to_be_clickable(driver, category_select_xpath)
        driver.find_element(By.XPATH, category_select_xpath).click()
        driver.find_element(By.XPATH, '//*[text()="推荐选择"]').click()
        driver.find_element(By.XPATH, '//*[text()="日常"]').click()

        # select_category(driver, "生活", "日常")  # Call the function to select the category and subcategory

        # Add Tags
        print("Adding tags...")
        tag_input_xpath = '//input[@placeholder="按回车键Enter创建标签"]'
        tags = ["视觉震撼", "自然", "奇观", "深度学习", "AI", "旅行", "美景"]
        for tag in tags:
            wait_for_element_to_be_clickable(driver, tag_input_xpath)
            driver.find_element(By.XPATH, tag_input_xpath).send_keys(tag)
            driver.find_element(By.XPATH, tag_input_xpath).send_keys(Keys.ENTER)
            time.sleep(1)

        # Prompt for Publishing
        user_input = input("Do you want to publish now? Type 'yes' to confirm: ").strip().lower()
        if user_input == 'yes':
            # Click Publish
            print("Publishing the video...")
            publish_button_xpath = '//*[text()="立即投稿"]'
            wait_for_element_to_be_clickable(driver, publish_button_xpath)
            driver.find_element(By.XPATH, publish_button_xpath).click()
            print("Video published successfully!")
        else:
            print("Publishing cancelled by the user.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Get the video and cover paths
    path_mp4, path_cover = get_media_paths(catalog_mp4)
    if not path_mp4 or not path_cover:
        print("Video or cover file not found. Exiting...")
    else:
        print(f"Found video path: {path_mp4}")
        print(f"Found cover path: {path_cover}")
        publish_bilibili(path_mp4, path_cover)
