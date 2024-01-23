import pathlib
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, NoSuchWindowException, TimeoutException

from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager

from utils import dismiss_alert, crop_and_resize_cover_image

import traceback

import time
import os
import requests
import base64
import os
import json



def download_image(url, local_path='./temp/'):
    response = requests.get(url)
    if response.status_code == 200:
        os.makedirs(local_path, exist_ok=True)
        filename = url.split('/')[-1].split('?')[0]
        file_path = os.path.join(local_path, filename)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        return file_path
    else:
        raise Exception(f"Error downloading image: Status code {response.status_code}")

# Function to call the API with base64 encoded image
def b64_api(username, password, img_path, ID):
    with open(img_path, 'rb') as f:
        b64_data = base64.b64encode(f.read())
    b64 = b64_data.decode()
    data = {"username": username, "password": password, "ID": ID, "b64": b64, "version": "3.1.1"}
    data_json = json.dumps(data)
    result = json.loads(requests.post("http://www.fdyscloud.com.cn/tuling/predict", data=data_json).text)

    # Save the result to a JSON file with the same base name as the image file
    base_name = os.path.splitext(os.path.basename(img_path))[0]  # Extracts filename without extension
    json_path = os.path.join(os.path.dirname(img_path), base_name + '.json')
    
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(result, json_file, ensure_ascii=False, indent=4)

    return result


class BilibiliPublisher:
    def __init__(self, driver, path_mp4, path_cover, metadata, test=False):
        self.driver = driver
        self.path_mp4 = path_mp4
        self.path_cover = path_cover
        self.metadata = metadata
        self.test = test

    def wait_for_element_to_be_clickable(self, xpath, timeout=600):
        time.sleep(3)
        # try:
        #     WebDriverWait(self.driver, timeout).until(
        #         EC.element_to_be_clickable((By.XPATH, xpath))
        #     )
        #     print(f"Element {xpath} is clickable.")
        # except TimeoutException:
        #     print(f"Timed out waiting for {xpath} to become clickable.")

    def solve_captcha(self):
        time.sleep(3)

        # Execute JavaScript to check if the CAPTCHA popup is present
        is_captcha_present = self.driver.execute_script("""
            return document.querySelector('.geetest_panel_box') !== null;
        """)
        
        max_retries = 5
        retry = 0
        while is_captcha_present and retry < max_retries:
            print("CAPTCHA detected. Solving...")
            # Execute JavaScript to get the CAPTCHA image URL
            captcha_image_url = self.driver.execute_script("""
                let captchaImageElement = document.querySelector('.geetest_item_wrap');
                return captchaImageElement ? captchaImageElement.style.backgroundImage.slice(5, -2) : '';
            """)

            if captcha_image_url:
                img_path = download_image(captcha_image_url)
                result = b64_api(username="lachlanchen", password="eG8h.YfnWMyd9QR", img_path=img_path, ID="08272733")
                print(result)

                # Use the result to simulate the clicks on the CAPTCHA image
                for key in [f'顺序{i}' for i in range(1, 10)]:  # Add more keys if there are more click points
                    if key in result['data']:
                        x = result['data'][key]['X坐标值']
                        y = result['data'][key]['Y坐标值']
                        # Execute JavaScript to simulate the click
                        self.driver.execute_script(f"""
                            let rect = document.querySelector('.geetest_item_wrap').getBoundingClientRect();
                            let clickX = rect.left + {x};
                            let clickY = rect.top + {y};
                            let clickEvent = new MouseEvent('click', {{
                                view: window,
                                bubbles: true,
                                cancelable: true,
                                clientX: clickX,
                                clientY: clickY
                            }});
                            document.elementFromPoint(clickX, clickY).dispatchEvent(clickEvent);
                        """)
                        time.sleep(1)  # Wait a second between clicks if needed

                # After solving CAPTCHA, click the confirm button
                self.driver.execute_script("""
                    let confirmButton = document.querySelector('.geetest_commit');
                    if (confirmButton) {
                        confirmButton.click();
                    }
                """)
                print("CAPTCHA solved and confirmed.")
            else:
                print("Failed to get CAPTCHA image URL.")

            

            try:
                time.sleep(3)
                is_captcha_present = self.driver.execute_script("""
                    return document.querySelector('.geetest_panel_box') !== null;
                """)
            except:
                print("CAPTCHA confirmed. ")
                is_captcha_present = False

            retry += 1

        else:
            print("No CAPTCHA detected.")

    def publish(self):
        driver = self.driver
        wait_for_element_to_be_clickable = self.wait_for_element_to_be_clickable
        path_mp4 = self.path_mp4
        path_cover = self.path_cover
        metadata = self.metadata
        test = self.test

        try:
            print("Starting the publishing process on Bilibili...")
            driver.get("https://member.bilibili.com/platform/upload/video/frame")
            time.sleep(1)
            dismiss_alert(driver)
            time.sleep(30)
            
            print(f"Uploading video from path: {path_mp4}")
            upload_input_xpath = '//input[@type="file" and contains(@accept,"mp4")]'
            time.sleep(3)        
            # wait_for_element_to_be_clickable(upload_input_xpath)
            driver.find_element(By.XPATH, upload_input_xpath).send_keys(path_mp4)

            print("Waiting for the video to be uploaded...")
            time.sleep(3)        
            WebDriverWait(driver, 3600).until(EC.presence_of_element_located((By.XPATH, '//*[text()="上传完成"]')))
            print("Video uploaded successfully!")

            print("Handling cover upload.")
            path_cover = crop_and_resize_cover_image(path_cover)
            # Click on the '更改封面' button to start the cover upload process
            edit_cover_button_xpath = '//*[text()="更改封面"]'
            time.sleep(3)
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, edit_cover_button_xpath))).click()
            # Wait for the '上传封面' option to become clickable and click it
            upload_cover_option_xpath = '//*[text()="上传封面"]'
            time.sleep(3)
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, upload_cover_option_xpath))).click()
            file_input_xpath = "//input[@type='file' and @accept='image/png, image/jpeg']"
            time.sleep(3)
            file_input_element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, file_input_xpath)))
            # Send the file path to the hidden file input element
            time.sleep(3)
            file_input_element.send_keys(path_cover)
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
            time.sleep(3)        
            result = driver.execute_script(js_code)
            # Print the result of the JavaScript execution
            print(result)
            print("Cover upload finished.")

            # Enter Title
            print("Entering title...")
            title_input_xpath = '//input[contains(@placeholder,"请输入稿件标题")]'
            time.sleep(3)        
            # wait_for_element_to_be_clickable(title_input_xpath)
            driver.find_element(By.XPATH, title_input_xpath).clear()
            time.sleep(3)        
            driver.find_element(By.XPATH, title_input_xpath).send_keys(metadata['title'])

            # Enter Description
            print("Entering description...")
            description_with_tags = metadata['long_description'] + " " + " ".join([f"#{tag}" for tag in metadata['tags']])
            desc_input_xpath = '//*[@editor_id="desc_at_editor"]//br'
            time.sleep(3)
            # wait_for_element_to_be_clickable(desc_input_xpath)
            driver.find_element(By.XPATH, desc_input_xpath).send_keys(description_with_tags)

            # Select Category
            print("Selecting category...")
            category_select_xpath = '//*[contains(@class,"select-item-cont")]'
            # wait_for_element_to_be_clickable(category_select_xpath)
            driver.find_element(By.XPATH, category_select_xpath).click()
            time.sleep(1)
            driver.find_element(By.XPATH, '//*[text()="推荐选择"]').click()
            time.sleep(1)
            driver.find_element(By.XPATH, '//*[text()="日常"]').click()
            # time.sleep(1)

            # Add Tags
            print("Adding tags...")
            tag_input_xpath = '//input[@placeholder="按回车键Enter创建标签"]'
            for tag in metadata['tags']:
                # wait_for_element_to_be_clickable(tag_input_xpath)
                time.sleep(1)
                driver.find_element(By.XPATH, tag_input_xpath).send_keys(tag)
                time.sleep(1)
                driver.find_element(By.XPATH, tag_input_xpath).send_keys(Keys.ENTER)

            # Prompt for Publishing
            if test:
                user_input = input("Do you want to publish now? Type 'yes' to confirm: ").strip().lower()
            else:
                user_input = "yes"
            if user_input == 'yes':
                # Click Publish
                print("Publishing the video...")
                publish_button_xpath = '//*[text()="立即投稿"]'
                # publish_button_xpath = '//*[text()="存草稿"]'
                time.sleep(10)
                # wait_for_element_to_be_clickable(publish_button_xpath)
                driver.find_element(By.XPATH, publish_button_xpath).click()

                time.sleep(10)
                self.solve_captcha()

                time.sleep(10)
                dismiss_alert(driver)
                time.sleep(3)

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
            "brief_description": "跟随我们的味蕾之旅，发现为何这款烤鸡让人赞不绝口！",
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
