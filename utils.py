from selenium.common.exceptions import NoAlertPresentException

import os
import subprocess

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment
from sendgrid.helpers.mail import FileContent, FileName, FileType, Disposition
import time
import os
import base64

class SendMail:
    # Set defaults within the class, but allow them to be overridden
    def __init__(self, sendgrid_api_key=os.environ.get('SENDGRID_API_KEY'), from_email='lachlan.miao.chen@gmail.com', to_email='lachlan.mia.chan@gmail.com'):
        self.sendgrid_api_key = sendgrid_api_key
        self.from_email = from_email
        self.to_email = to_email

    def send_email(self, subject, content, attachment_path, attachment_name):
        sg = SendGridAPIClient(self.sendgrid_api_key)
        mail = Mail(
            from_email=Email(self.from_email),
            to_emails=To(self.to_email),
            subject=subject,
            plain_text_content=content
        )

        with open(attachment_path, 'rb') as f:
            data = f.read()
            encoded_file = base64.b64encode(data).decode()

        attachment = Attachment()
        attachment.file_content = FileContent(encoded_file)
        attachment.file_type = FileType('image/png')
        attachment.file_name = FileName(attachment_name)
        attachment.disposition = Disposition('attachment')
        mail.add_attachment(attachment)

        response = sg.send(mail)
        print(f"Email sent, status code: {response.status_code}")

def dismiss_alert(driver, dismiss=False):
    try:
        alert = driver.switch_to.alert
        if dismiss:
            alert.dismiss()
        else:
            alert.accept()  # Use alert.accept() if you want to accept the alert.
        print("Alert was present and dismissed.")
    except NoAlertPresentException:
        print("No alert present.")

def crop_and_resize_cover_image(path_cover):
    # Define the base name and create a name for the resized cover
    base_name = os.path.basename(path_cover)
    name, ext = os.path.splitext(base_name)
    resized_name = f"{name}_resized{ext}"
    path_cover_resized = os.path.join(os.path.dirname(path_cover), resized_name)
    
    # FFmpeg command to crop and resize the image
    ffmpeg_command = [
        '/usr/local/bin/ffmpeg',
        '-y',
        '-i', path_cover,  # Input file
        '-vf', 'crop=in_w:in_h*3/4,scale=1200:900',  # Crop and scale filter
        path_cover_resized  # Output file
    ]

    # Execute the FFmpeg command
    try:
        subprocess.run(ffmpeg_command, check=True)
        print(f"Resized image saved to {path_cover_resized}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred during the resizing process: {e}")
        return None
    
    return path_cover_resized

def bring_to_front(window_name_pattern):
    try:
        # List all Chromium windows
        window_list = subprocess.check_output(["xdotool", "search", "--name", "Chromium"]).decode().strip().split('\n')
        # Iterate through the list of window IDs
        for window_id in window_list:
            # Get the name of each window using its ID
            window_name = subprocess.check_output(["xdotool", "getwindowname", window_id]).decode().strip()
            # Check if the window name matches any of the patterns provided
            if any(text in window_name for text in window_name_pattern):
                # If a match is found, activate the window
                subprocess.run(["xdotool", "windowactivate", "--sync", window_id])
                # Optionally, add a brief pause to ensure the window comes to the front
                subprocess.run(["sleep", "1"])
                break  # Exit the loop after the first match
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.output.decode()}")