import selenium
from selenium import webdriver
import pathlib
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, NoSuchWindowException, TimeoutException
from selenium.common.exceptions import NoSuchElementException, NoSuchWindowException, TimeoutException, NoAlertPresentException


# Constants
catalog_mp4 = r"/Users/lachlan/Documents/iProjects/auto-publish/videos"
describe = "裸眼3D看蜘蛛侠 #搞笑 #电影 #视觉震撼"

# Function to dismiss an alert if present
def dismiss_alert(driver):
    try:
        alert = driver.switch_to.alert
        alert.dismiss()
        print("Alert was present and dismissed.")
    except NoAlertPresentException:
        print("No alert present.")

# Initialize Chrome options
options = webdriver.ChromeOptions()
options.add_experimental_option("debuggerAddress", "127.0.0.1:5003")
options.add_argument("--no-sandbox")  # Bypass OS security model
options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
options.add_argument("--disable-gpu")  # Applicable to windows os only
options.add_argument("--disable-extensions")  # Disable extensions
options.add_argument("--start-maximized")  # Start maximized
driver = webdriver.Chrome(options=options)

# Ensure no alert is blocking the script
dismiss_alert(driver)

# Function to get the video and cover paths
def get_media_paths(catalog):
    path = pathlib.Path(catalog)
    path_mp4 = next((str(p) for p in path.glob('*.mp4')), None)
    path_cover = next((str(p) for p in path.glob('*') if p.suffix in ['.png', '.jpg']), None)
    return path_mp4, path_cover

# Function to wait until the element is truly interactable
def wait_for_element_to_be_clickable(driver, xpath, timeout=600):
    time.sleep(3)

    # don't change this, i want a separate function but still use sleep as placeholder

    # try:
    #     WebDriverWait(driver, timeout).until(
    #         lambda d: d.find_element(By.XPATH, xpath).is_displayed() and
    #                   d.find_element(By.XPATH, xpath).is_enabled()
    #     )
    #     print(f"Element {xpath} is truly interactable.")
    # except TimeoutException:
    #     print(f"Timed out waiting for {xpath} to become interactable.")

# Function to publish video on Douyin
def publish_douyin(path_mp4, path_cover):
    try:
        print("Starting the publishing process on Douyin...")
        driver.get("https://creator.douyin.com/creator-micro/home")
        wait_for_element_to_be_clickable(driver, '//*[text()="发布作品"]')
        driver.find_element(By.XPATH, '//*[text()="发布作品"]').click()
        wait_for_element_to_be_clickable(driver, '//*[text()="发布视频"]')
        driver.find_element(By.XPATH, '//*[text()="发布视频"]').click()
        wait_for_element_to_be_clickable(driver, '//input[@type="file"]')
        driver.find_element(By.XPATH, '//input[@type="file"]').send_keys(path_mp4)

        print("Waiting for the video to be uploaded...")
        WebDriverWait(driver, 600).until(EC.presence_of_element_located((By.XPATH, '//*[text()="重新上传"]')))
        print("Video uploaded successfully!")

        print("Adding cover...")
        wait_for_element_to_be_clickable(driver, '//*[text()="选择封面"]')
        driver.find_element(By.XPATH, '//*[text()="选择封面"]').click()
        wait_for_element_to_be_clickable(driver, '//div[text()="上传封面"]')
        driver.find_element(By.XPATH, '//div[text()="上传封面"]').click()
        wait_for_element_to_be_clickable(driver, '//*[text()="点击上传 或直接将图片文件拖入此区域"]/../../../..//input[@type="file"]')
        driver.find_element(By.XPATH, '//*[text()="点击上传 或直接将图片文件拖入此区域"]/../../../..//input[@type="file"]').send_keys(path_cover)

        # Wait for the '完成' button to be clickable and ensure it's scrolled into view
        finish_button_xpath = '//button[contains(@class, "finish--3_3_P")]/span[contains(text(), "完成")]'
        wait_for_element_to_be_clickable(driver, finish_button_xpath)
        finish_button = driver.find_element(By.XPATH, finish_button_xpath)
        driver.execute_script("arguments[0].scrollIntoView(true);", finish_button)

        # If there's an overlay or loading animation, handle it here
        # ...

        # Check if the button is clickable before attempting to click
        if finish_button.is_displayed() and finish_button.is_enabled():
            finish_button.click()
        else:
            print("Finish button is not clickable.")

         # Entering the title
        print("Entering the title...")
        title_input_xpath = '//input[@placeholder="好的作品标题可获得更多浏览"]'
        wait_for_element_to_be_clickable(driver, title_input_xpath)
        title_input_element = driver.find_element(By.XPATH, title_input_xpath)
        title_input_element.clear()  # Clearing any pre-filled text
        title_input_element.send_keys(describe.split(" #")[0])  # Using the first part of the 'describe' variable as the title



        print("Entering video description...")
        description_input_xpath = '//div[@data-placeholder="添加作品简介"]'
        wait_for_element_to_be_clickable(driver, description_input_xpath)
        description_input_element = driver.find_element(By.XPATH, description_input_xpath)
        driver.execute_script("arguments[0].innerText = arguments[1];", description_input_element, describe + " #上热门 #dou上热门 #我要上热门")


        print("Entering location information...")
        wait_for_element_to_be_clickable(driver, '//*[text()="输入地理位置"]')
        driver.find_element(By.XPATH, '//*[text()="输入地理位置"]').click()
        wait_for_element_to_be_clickable(driver, '//*[text()="输入地理位置"]/..//input')
        driver.find_element(By.XPATH, '//*[text()="输入地理位置"]/..//input').send_keys("香港大学")
        wait_for_element_to_be_clickable(driver, '//*[@class="semi-popover-content"]//*[text()="香港大学"]')
        driver.find_element(By.XPATH, '//*[@class="semi-popover-content"]//*[text()="香港大学"]').click()


         # Handling the "今日头条" switch
        print("Handling '今日头条' switch...")
        toutiao_switch_xpath = "//div[contains(@class, 'toutiao--1ujZn')]/following-sibling::div//input[@type='checkbox' and @role='switch']"
        wait_for_element_to_be_clickable(driver, toutiao_switch_xpath)
        toutiao_switch_element = driver.find_element(By.XPATH, toutiao_switch_xpath)
        driver.execute_script("arguments[0].scrollIntoView(true);", toutiao_switch_element)

        # Check the current state of the switch (whether it's checked or not)
        is_switch_active = toutiao_switch_element.is_selected()
        
        # If you want the switch to be ON, but it's currently OFF, click it (or vice versa)
        if not is_switch_active:  # Change condition based on your requirement
            try:
                toutiao_switch_element.click()
            except Exception:
                # If standard click doesn't work, use JavaScript to click
                driver.execute_script("arguments[0].click();", toutiao_switch_element)
            print("'今日头条' switch is now ON.")
        else:
            print("'今日头条' switch is already in the desired state.")
        
        # Optionally, recheck the state to confirm
        is_switch_active = toutiao_switch_element.is_selected()
        if is_switch_active:
            print("Confirmed: '今日头条' switch is ON.")
        else:
            print("Check failed: '今日头条' switch did not turn ON.")
            
        # Prompt for manual check and publish
        user_input = input("Do you want to publish now? Type 'yes' to confirm: ").strip().lower()
        if user_input == 'yes':
            print("Publishing the video...")
            wait_for_element_to_be_clickable(driver, '//button[text()="发布"]')
            driver.find_element(By.XPATH, '//button[text()="发布"]').click()
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
        publish_douyin(path_mp4, path_cover)
