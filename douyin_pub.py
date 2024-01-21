import selenium
from selenium import webdriver
import pathlib
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, NoSuchWindowException, TimeoutException, NoAlertPresentException

from utils import dismiss_alert
import traceback

class DouyinPublisher:
    def __init__(self, driver, path_mp4, path_cover, metadata):
        self.driver = driver
        self.path_mp4 = path_mp4
        self.path_cover = path_cover
        self.metadata = metadata

    def wait_for_element_to_be_clickable(self, xpath, timeout=600):
        time.sleep(3)

    # def dismiss_alert(self):
    #     try:
    #         alert = self.driver.switch_to.alert
    #         alert.accept()
    #         print("Alert was present and dismissed.")
    #     except NoAlertPresentException:
    #         print("No alert present.")

    def publish(self):
        try:
            driver = self.driver
            path_mp4 = self.path_mp4
            path_cover = self.path_cover
            metadata = self.metadata
            wait_for_element_to_be_clickable = self.wait_for_element_to_be_clickable
            # dismiss_alert = self.dismiss_alert

            print("Starting the publishing process on Douyin...")
            driver.get("https://creator.douyin.com/creator-micro/home")
            time.sleep(1)
            dismiss_alert(driver)
            time.sleep(30)

            wait_for_element_to_be_clickable(driver, '//*[text()="发布作品"]')
            driver.find_element(By.XPATH, '//*[text()="发布作品"]').click()
            wait_for_element_to_be_clickable(driver, '//*[text()="发布视频"]')
            driver.find_element(By.XPATH, '//*[text()="发布视频"]').click()
            wait_for_element_to_be_clickable(driver, '//input[@type="file"]')
            driver.find_element(By.XPATH, '//input[@type="file"]').send_keys(path_mp4)

            print("Waiting for the video to be uploaded...")
            WebDriverWait(driver, 3600).until(EC.presence_of_element_located((By.XPATH, '//*[text()="重新上传"]')))
            print("Video uploaded successfully!")

            print("Adding cover...")
            wait_for_element_to_be_clickable(driver, '//*[text()="选择封面"]')
            driver.find_element(By.XPATH, '//*[text()="选择封面"]').click()
            wait_for_element_to_be_clickable(driver, '//div[text()="上传封面"]')
            driver.find_element(By.XPATH, '//div[text()="上传封面"]').click()
            wait_for_element_to_be_clickable(driver, '//*[text()="点击上传 或直接将图片文件拖入此区域"]/../../../..//input[@type="file"]')
            driver.find_element(By.XPATH, '//*[text()="点击上传 或直接将图片文件拖入此区域"]/../../../..//input[@type="file"]').send_keys(path_cover)

            # # Wait for the '完成' button to be clickable and ensure it's scrolled into view
            # finish_button_xpath = '//button[contains(@class, "finish--3_3_P")]/span[contains(text(), "完成")]'
            # wait_for_element_to_be_clickable(driver, finish_button_xpath)
            # finish_button = driver.find_element(By.XPATH, finish_button_xpath)
            # driver.execute_script("arguments[0].scrollIntoView(true);", finish_button)


            # # Check if the button is clickable before attempting to click
            # if finish_button.is_displayed() and finish_button.is_enabled():
            #     finish_button.click()
            # else:
            #     print("Finish button is not clickable.")

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

            # Execute the script
            button_clicked = driver.execute_script(click_finish_button_script)

            # Handle the result
            if button_clicked:
                print("Clicked the '完成' button successfully.")
            else:
                print("Could not find the '完成' button.")

            time.sleep(5)

             # Entering the title
            print("Entering the title...")
            title_input_xpath = '//input[@placeholder="好的作品标题可获得更多浏览"]'
            wait_for_element_to_be_clickable(driver, title_input_xpath)
            title_input_element = driver.find_element(By.XPATH, title_input_xpath)
            title_input_element.clear()  # Clearing any pre-filled text
            # title_input_element.send_keys(describe.split(" #")[0])  # Using the first part of the 'describe' variable as the title
            title_input_element.send_keys(metadata["title"])  # Using the first part of the 'describe' variable as the title



            print("Entering video description...")
            description_input_xpath = '//div[@data-placeholder="添加作品简介"]'
            wait_for_element_to_be_clickable(driver, description_input_xpath)
            description_input_element = driver.find_element(By.XPATH, description_input_xpath)
            description_with_tags = metadata['long_description'] + " " + " ".join([f"#{tag}" for tag in metadata['tags']])
            driver.execute_script("arguments[0].innerText = arguments[1];", description_input_element,  description_with_tags + " #上热门 #dou上热门 #我要上热门")


            print("Entering location information...")
            wait_for_element_to_be_clickable(driver, '//*[text()="输入地理位置"]')
            driver.find_element(By.XPATH, '//*[text()="输入地理位置"]').click()
            wait_for_element_to_be_clickable(driver, '//*[text()="输入地理位置"]/..//input')
            driver.find_element(By.XPATH, '//*[text()="输入地理位置"]/..//input').send_keys("香港大学")
            wait_for_element_to_be_clickable(driver, '//*[@class="semi-popover-content"]//*[text()="香港大学"]')
            driver.find_element(By.XPATH, '//*[@class="semi-popover-content"]//*[text()="香港大学"]').click()


            # # Handling the "今日头条" switch
            # print("Handling '今日头条' switch...")
            # toutiao_switch_xpath = "//div[contains(@class, 'toutiao--1ujZn')]/following-sibling::div//input[@type='checkbox' and @role='switch']"
            # wait_for_element_to_be_clickable(driver, toutiao_switch_xpath)
            # toutiao_switch_element = driver.find_element(By.XPATH, toutiao_switch_xpath)
            # driver.execute_script("arguments[0].scrollIntoView(true);", toutiao_switch_element)

            # # Check the current state of the switch (whether it's checked or not)
            # is_switch_active = toutiao_switch_element.is_selected()
            
            # # If you want the switch to be ON, but it's currently OFF, click it (or vice versa)
            # if not is_switch_active:  # Change condition based on your requirement
            #     try:
            #         toutiao_switch_element.click()
            #     except Exception:
            #         # If standard click doesn't work, use JavaScript to click
            #         driver.execute_script("arguments[0].click();", toutiao_switch_element)
            #     print("'今日头条' switch is now ON.")
            # else:
            #     print("'今日头条' switch is already in the desired state.")
            
            # # Optionally, recheck the state to confirm
            # is_switch_active = toutiao_switch_element.is_selected()
            # if is_switch_active:
            #     print("Confirmed: '今日头条' switch is ON.")
            # else:
            #     print("Check failed: '今日头条' switch did not turn ON.")

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
                
                # If you want to toggle the switch and you are sure it's safe to do so
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
                driver.execute_script(toggle_script)
                print("Toggled the '原创内容' switch.")
            else:
                print("Could not find '原创内容' switch.")
                
            # Prompt for manual check and publish
            # user_input = input("Do you want to publish now? Type 'yes' to confirm: ").strip().lower()
            user_input = "yes"
            if user_input == 'yes':
                print("Publishing the video...")
                wait_for_element_to_be_clickable(driver, '//button[text()="发布"]')
                driver.find_element(By.XPATH, '//button[text()="发布"]').click()

                time.sleep(10)

                dismiss_alert(driver)
                
                print("Video published successfully!")
            else:
                print("Publishing cancelled by the user.")
        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()

# Rest of your code for initialization and running the publisher

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
            "description": "跟随我们的味蕾之旅，发现为何这款烤鸡让人赞不绝口！",
            "tags": ["美食", "烤鸡", "推荐"]
        }

        # Create an instance of the DouyinPublisher
        douyin_publisher = DouyinPublisher(
            driver=driver,
            path_mp4=path_mp4,
            path_cover=path_cover,
            metadata=metadata
        )

        # Start publishing process
        douyin_publisher.publish()
