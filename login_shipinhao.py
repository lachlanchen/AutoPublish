from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment
# from sendgrid.helpers.mail import FileContent, FileName, FileType, Disposition
import time
import os
import base64

from utils import SendMail
from utils import dismiss_alert, bring_to_front

# class SendMail:
#     # Set defaults within the class, but allow them to be overridden
#     def __init__(self, sendgrid_api_key=os.environ.get('SENDGRID_API_KEY'), from_email=os.environ.get('FROM_EMAIL'), to_email=os.environ.get('TO_EMAIL')):
#         self.sendgrid_api_key = sendgrid_api_key
#         self.from_email = from_email
#         self.to_email = to_email

#     def send_email(self, subject, content, attachment_path, attachment_name):
#         sg = SendGridAPIClient(self.sendgrid_api_key)
#         mail = Mail(
#             from_email=Email(self.from_email),
#             to_emails=To(self.to_email),
#             subject=subject,
#             plain_text_content=content
#         )

#         with open(attachment_path, 'rb') as f:
#             data = f.read()
#             encoded_file = base64.b64encode(data).decode()

#         attachment = Attachment()
#         attachment.file_content = FileContent(encoded_file)
#         attachment.file_type = FileType('image/png')
#         attachment.file_name = FileName(attachment_name)
#         attachment.disposition = Disposition('attachment')
#         mail.add_attachment(attachment)

#         response = sg.send(mail)
#         print(f"Email sent, status code: {response.status_code}")

class ShiPinHaoLogin:
    def __init__(self, driver=None, port="5003"):
        print("Initializing ShiPinHaoLogin class...")
        self.mailer = SendMail()  # Using default parameters
        self.port = port
        self.driver = driver if driver else self.create_new_driver()

    def create_new_driver(self):
        print("Creating new WebDriver instance...")
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.port}")
        driver = webdriver.Chrome(options=options)
        return driver

    def find_lazying_art(self):
        try:
            # Search for the span element containing the specific text
            # Adjusted the XPath to target the class and text more accurately based on the provided structure
            user_info_element = self.driver.find_element(By.XPATH, "//span[contains(@class, 'name') and contains(text(), '陈苗LazyingArt懒人艺术')]")
            if user_info_element:
                print("Found '陈苗LazyingArt懒人艺术'.")
                return True
        except NoSuchElementException:
            # If the element is not found, NoSuchElementException is caught
            print("Did not find '陈苗LazyingArt懒人艺术'.")
        return False


    def check_and_act(self):
        print("Navigating to the URL...")
        bring_to_front(["视频号"])

        url = 'https://channels.weixin.qq.com/platform/post/create'
        self.driver.get(url)

        time.sleep(1)

        dismiss_alert(self.driver)

        time.sleep(3)

        bring_to_front(["视频号"])

        if self.find_lazying_art():
            print("Already logged in. ")
            return


        try:
            WebDriverWait(self.driver, 20).until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, 'iframe.display')))
            self.take_screenshot_and_send_email()
        except TimeoutException:
            print("Already logged in or the page did not load as expected.")
            return  # Exiting the method early if we're already logged in or if the iframe is not present.



        end_time = time.time() + 600  # 30 minutes from now
        last_refresh_time = time.time()
        last_email_time = time.time() - 30  # Initialize to send email immediately

        while time.time() < end_time:
            current_time = time.time()
        
            if self.is_qr_outdated() or (current_time - last_email_time >= 180):
                print("QR code is outdated, refreshing...")
                self.driver.refresh()
                time.sleep(5)
                self.take_screenshot_and_send_email()
                WebDriverWait(self.driver, 20).until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, 'iframe.display')))
                last_refresh_time = time.time()

            # if time.time() - last_email_time >= 60:  # Take screenshot and send email every 60 seconds
            #     print("Taking screenshot and sending email...")
            #     self.take_screenshot_and_send_email()
            #     last_email_time = time.time()

            if self.needs_login():
                print("Login required, will check again in 5 seconds...")
                time.sleep(5)  # Check again in 5 seconds
            else:
                print("Logged in successfully, stopping checks.")
                break  # Break the loop if logged in

        # self.driver.quit()

    # def is_qr_outdated(self):
    #     elements = self.driver.find_elements(By.CSS_SELECTOR, ".refresh-wrap .refresh-tip")
    #     for element in elements:
    #         if element.text == "二维码已过期，点击刷新":
    #             return True
    #     return False
    def is_qr_outdated(self):
        try:
            # Look for the more specific structure - a visible mask containing the refresh message
            elements = self.driver.find_elements(By.CSS_SELECTOR, ".mask.show .refresh-tip")
            for element in elements:
                if "二维码已过期" in element.text:
                    return True
                    
            # Alternative approach - check if the mask with refresh is visible
            outdated_masks = self.driver.find_elements(By.CSS_SELECTOR, ".mask.show")
            for mask in outdated_masks:
                refresh_tips = mask.find_elements(By.CSS_SELECTOR, ".refresh-tip")
                for tip in refresh_tips:
                    if "二维码已过期" in tip.text:
                        return True
                        
            return False
        except Exception as e:
            print(f"Error checking if QR is outdated: {e}")
            return False

    def needs_login(self):
        elements = self.driver.find_elements(By.CSS_SELECTOR, ".tip span")
        for element in elements:
            if element.text == "微信扫码登录 视频号助手":
                return True
        return False

    def take_screenshot_and_send_email(self):
        screenshot_path = '/tmp/shipinhao-screenshot.png'
        self.driver.save_screenshot(screenshot_path)
        self.mailer.send_email(
            'Shipinhao Login Required',
            'Login is required. Please see the attached screenshot.',
            screenshot_path,
            'shipinhao-screenshot.png'
        )

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="5006", help="Chrome debugging port")
    args = parser.parse_args()

    shi_pin_hao_login = ShiPinHaoLogin(port=args.port)
    shi_pin_hao_login.check_and_act()
