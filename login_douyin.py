from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from utils import SendMail
from utils import dismiss_alert, bring_to_front


class DouyinLogin:
    def __init__(self, driver=None):
        print("Initializing DouyinLogin class...")
        self.mailer = SendMail()  # Ensure SendMail is defined elsewhere and fully functional
        self.driver = driver if driver else self.create_new_driver()

    def create_new_driver(self):
        print("Creating new WebDriver instance...")
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:5004")
        driver = webdriver.Chrome(options=options)
        return driver

    def check_and_act(self):

        print("Checking login status...")
        if self.is_already_logged_in():
            print("Already logged in.")
            return
        
        print("Navigating to the Douyin URL...")
        url = 'https://creator.douyin.com/creator-micro/home'
        self.driver.get(url)

        time.sleep(1)

        dismiss_alert(self.driver)

        time.sleep(3)

        bring_to_front(["抖音"])

        try:
            login_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'span.login'))
            )
            login_button.click()

            
            time.sleep(5)  # Allow some time for the QR code to load

            WebDriverWait(self.driver, 20).until(
                lambda d: d.execute_script(
                    "return [...document.querySelectorAll('img')].some(img => img.src.startsWith('data:image/png;base64'))"
                )
            )

            self.take_screenshot_and_send_email()
        except Exception:
            print("Login button not found, maybe already logged in.")

        

        # The rest of your code for taking screenshots and email notifications...

        start_time = time.time()
        while time.time() - start_time < 600:  # 10 minutes
            if self.is_qr_outdated():
                self.refresh_qr_code()
                time.sleep(5)  # Wait for the QR code to refresh
                self.take_screenshot_and_send_email()

            if self.is_already_logged_in():
                print("Logged in successfully, stopping checks.")
                break

            time.sleep(5)

    def is_already_logged_in(self):
        # Check for specific text that indicates we are logged in
        return bool(self.driver.find_elements(By.XPATH, "//div[text()='陈苗LazyingArt懒人艺术']"))

    def is_qr_outdated(self):
        # Check if the error message indicating an outdated QR code is present by text content
        outdated_text = "二维码已失效，点击刷新"
        return bool(self.driver.find_elements(By.XPATH, f"//p[contains(text(), '{outdated_text}')]"))

    def refresh_qr_code(self):
        print("QR code is outdated, attempting to refresh...")
        # Use JavaScript to click the refresh button
        self.driver.execute_script(
            """
            let overlayContainers = document.querySelectorAll('div[class*="-vmock-tabs-pane-motion-overlay"]');
            overlayContainers.forEach(container => {
                let refreshButton = container.querySelector('img[src^="data:image/svg+xml"]');
                if (refreshButton) {
                    refreshButton.click();
                }
            });
            """
        )
        print("Refresh click attempted.")

    def take_screenshot_and_send_email(self):
        screenshot_path = '/tmp/douyin-login.png'
        self.driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}.")
        self.mailer.send_email(
            'Douyin Login Required',
            'Login is required. Please see the attached screenshot including the QR code.',
            screenshot_path,
            'douyin-login.png'
        )

if __name__ == "__main__":
    douyin_login = DouyinLogin()
    douyin_login.check_and_act()
