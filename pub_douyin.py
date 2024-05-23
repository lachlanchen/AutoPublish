import selenium
from selenium import webdriver
import pathlib
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, NoSuchWindowException, TimeoutException, NoAlertPresentException
from selenium.common.exceptions import WebDriverException


from utils import dismiss_alert, bring_to_front
from login_douyin import DouyinLogin

import traceback



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

                # Uploading the video
                print("Uploading video...")
                time.sleep(3)
                driver.find_element(By.XPATH, '//input[@type="file"]').send_keys(path_mp4)

                # Monitor upload status
                print("Waiting for the video to be uploaded...")
                reupload_xpath = '//*[text()="重新上传"]'
                # reupload_xpath = '//*[contains(text(),"重新上传")]'
                failure_xpath = '//*[text()="上传失败，重新上传"]'
                # failure_xpath = '//*[contains(text(),"上传失败")]'
                time.sleep(3)
                # WebDriverWait(driver, 3600).until(EC.presence_of_element_located((By.XPATH, '//*[text()="重新上传"]')))
                start_time = time.time()
                timeout = 3600  # 3600 seconds timeout
                
                while True:
                    if time.time() - start_time > timeout:
                        raise Exception("Timeout reached while waiting for video to be uploaded or for a failure message.")

                    try:
                        # Wait until the "重新上传" element is present
                        element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, reupload_xpath)))
                        print("Video upload prompt for 'Re-upload' detected, indicating upload completion.")
                        break
                    except:
                        pass  # Ignore TimeoutException here

                    try:
                        # Wait until the "上传失败" element is present
                        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, failure_xpath)))
                        print("Upload failed! Raising an error to initiate retry...")
                        
                    except:
                        # pass  # Ignore TimeoutException here
                        raise Exception("Video upload failed.")

                    time.sleep(5)  # Wait a bit before checking again

                print("Adding cover...")
                time.sleep(3)
                # wait_for_element_to_be_clickable(driver, '//*[text()="选择封面"]')
                driver.find_element(By.XPATH, '//*[text()="选择封面"]').click()
                time.sleep(3)
                # wait_for_element_to_be_clickable(driver, '//div[text()="上传封面"]')
                driver.find_element(By.XPATH, '//div[text()="上传封面"]').click()
                time.sleep(3)
                # wait_for_element_to_be_clickable(driver, '//*[text()="点击上传 或直接将图片文件拖入此区域"]/../../../..//input[@type="file"]')
                driver.find_element(By.XPATH, '//*[text()="点击上传 或直接将图片文件拖入此区域"]/../../../..//input[@type="file"]').send_keys(path_cover)

                

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
                title_input_xpath = '//input[@placeholder="好的作品标题可获得更多浏览"]'
                time.sleep(3)
                # wait_for_element_to_be_clickable(driver, title_input_xpath)
                title_input_element = driver.find_element(By.XPATH, title_input_xpath)
                time.sleep(3)
                title_input_element.clear()  # Clearing any pre-filled text
                # title_input_element.send_keys(describe.split(" #")[0])  # Using the first part of the 'describe' variable as the title
                time.sleep(3)
                title_input_element.send_keys(metadata["title"][:30])  # Using the first part of the 'describe' variable as the title



                print("Entering video description...")
                description_input_xpath = '//div[@data-placeholder="添加作品简介"]'
                time.sleep(3)
                # wait_for_element_to_be_clickable(driver, description_input_xpath)
                description_input_element = driver.find_element(By.XPATH, description_input_xpath)
                description_with_tags = metadata['long_description'] + " " + " ".join([f"#{tag}" for tag in metadata['tags']]) + " #上热门 #dou上热门 #我要上热门"
                time.sleep(3)
                driver.execute_script("arguments[0].innerText = arguments[1];", description_input_element,  description_with_tags[:1000])


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
                    time.sleep(3)
                    driver.execute_script(toggle_script)
                    print("Toggled the '原创内容' switch.")
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
                    driver.find_element(By.XPATH, '//button[text()="发布"]').click()
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
