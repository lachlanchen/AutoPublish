from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
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
#     def __init__(self, sendgrid_api_key=os.environ.get('SENDGRID_API_KEY'), from_email='lachlan.miao.chen@gmail.com', to_email='lachlan.mia.chan@gmail.com'):
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

class XiaoHongShuLogin:
    def __init__(self, driver=None, port="5003"):
        print("Initializing XiaoHongShuLogin class...")
        self.mailer = SendMail()  # Using default parameters
        self.port = port
        self.driver = driver if driver else self.create_new_driver()
        self.refresh_count = 0

    def create_new_driver(self):
        print("Creating new WebDriver instance...")
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.port}")
        driver = webdriver.Chrome(options=options)
        return driver

    def show_qr(self):
        """Attempt to reveal the QR code directly using WebDriver with a structural-based approach."""
        try:
            # Wait for the container to ensure the page has loaded
            WebDriverWait(self.driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.login-box-container')))
            # Use XPath to navigate to the QR button based on structure
            qr_button_xpath = "//div[contains(@class, 'login-box-container')]//img[contains(@src, 'data:image/png;base64')]"
            qr_button = self.driver.find_element(By.XPATH, qr_button_xpath)
            qr_button.click()
            print("QR code reveal attempted using WebDriver.")
        except Exception as e:
            print(f"Attempting to reveal QR code using JavaScript due to failure: {e}")
            self.show_qr_with_js()



    def show_qr_with_js(self):
        """Attempt to reveal the QR code using JavaScript with a structural-based approach."""
        qr_reveal_script = """
        var qrButtons = document.querySelectorAll("div.login-box-container img[src*='data:image/png;base64']");
        if (qrButtons.length > 0) {
            qrButtons[0].click();  // Assuming the first found QR button is the correct one
        } else {
            console.error('QR reveal button not found using JavaScript.');
        }
        """
        try:
            self.driver.execute_script(qr_reveal_script)
            print("Attempted to reveal QR code using JavaScript.")
        except Exception as e:
            print(f"Failed to reveal QR code using JavaScript: {e}")

    def find_lazying_art(self):
        try:
            # Search for the span element containing the specific text
            user_info_element = self.driver.find_element(By.XPATH, "//span[contains(text(), '陈苗LazyingArt懒人艺术')]")
            if user_info_element:
                print("Found '陈苗LazyingArt懒人艺术'.")
                return True
        except NoSuchElementException:
            # If the element is not found, NoSuchElementException is caught
            print("Did not find '陈苗LazyingArt懒人艺术'.")
        return False


    def check_and_act(self):
        print("Navigating to the XiaoHongShu login page...")

        bring_to_front(["小红书", "你访问的页面不见了"])

        url = 'https://creator.xiaohongshu.com/creator/home'
        self.driver.get(url)



        time.sleep(1)

        dismiss_alert(self.driver)

        time.sleep(3)

        bring_to_front(["小红书", "你访问的页面不见了"])

        if self.find_lazying_art():
            return


        try:
            WebDriverWait(self.driver, 30).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.login-box-container')))
            

            # # Click on the top right corner of the SMS login box to reveal the QR code
            # qr_button = self.driver.find_element(By.CSS_SELECTOR, 'img.css-wemwzq')
            # ActionChains(self.driver).click(qr_button).perform()

            self.show_qr()

            # Wait a few seconds for the QR code to be fully loaded and visible
            time.sleep(1)  # Adjust timing based on actual page behavior

            self.take_screenshot_and_send_email()
            
        except TimeoutException:
            print("Already logged in or the page did not load as expected.")
            return

        end_time = time.time() + 3600  # 30 minutes from now
        last_refresh_time = time.time()
        last_email_time = time.time() - 30  # Initialize to send email immediately

        while time.time() < end_time:
            if self.is_qr_outdated():
                print("QR code is outdated, attempting to refresh...")
                # self.refresh_qr_code()
                # self.driver.refresh()
                self.refresh_qr_code()
                time.sleep(3)
                self.take_screenshot_and_send_email()
                last_refresh_time = time.time()

            if time.time() - last_email_time >= 60:  # Take screenshot and send email every 60 seconds
                print("Taking screenshot and sending email...")
                time.sleep(3)
                self.take_screenshot_and_send_email()
                last_email_time = time.time()

            if not self.needs_login():
                print("Logged in successfully, stopping checks.")
                break  # Break the loop if logged in

            time.sleep(5)  # Wait for 5 seconds before checking again

    def is_qr_outdated(self):
        outdated_message = "二维码已失效，请刷新"
        return bool(self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{outdated_message}')]"))

    def refresh_qr_code(self):
        try:
            if self.refresh_count % 2:
                raise Exception("Default method failed in last attempt. ")

            # Locate the refresh button by its text and click it using JavaScript
            refresh_button_script = """
            var buttons = document.querySelectorAll('button');
            var buttonClicked = false;
            for (var i = 0; i < buttons.length; i++) {
                if (buttons[i].querySelector('span.btn-content') && buttons[i].querySelector('span.btn-content').textContent.trim() === '刷新') {
                    buttons[i].click();
                    buttonClicked = true;
                    break;
                }
            }
            return buttonClicked;
            """

            # Execute the script
            buttonClicked = self.driver.execute_script(refresh_button_script)

            # Check if the button was clicked successfully
            if buttonClicked:
                print("QR code refreshed successfully.")
                self.refresh_count += 1
            else:
                print("Refresh button not found.")
                raise Exception("Refresh button not found. ")

            

        except Exception as e:
            print(f"Direct refresh failed, attempting alternative method: {e}")
            # If clicking the refresh button fails, refresh the page
            self.driver.refresh()
            # Wait for the login box to become visible again
            WebDriverWait(self.driver, 30).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.login-box-container')))
            
            self.show_qr()

            self.refresh_count = 0
            
    def needs_login(self):
        try:
            WebDriverWait(self.driver, 30).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.login-box-container')))
            print("SMS login box detected, login is required.")
            return True
        except TimeoutException:
            print("No SMS login box detected, might already be logged in or the page did not load as expected.")
            return False

    def take_screenshot_and_send_email(self):
        screenshot_path = '/tmp/xiaohongshu-login.png'
        self.driver.save_screenshot(screenshot_path)
        self.mailer.send_email(
            'XiaoHongShu Login Required',
            'Login is required. Please see the attached screenshot including the QR code.',
            screenshot_path,
            'xiaohongshu-login.png'
        )

if __name__ == "__main__":
    xhs_login = XiaoHongShuLogin()
    xhs_login.check_and_act()
