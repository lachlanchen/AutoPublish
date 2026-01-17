from selenium.common.exceptions import NoAlertPresentException

import os
import subprocess

# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment
# from sendgrid.helpers.mail import FileContent, FileName, FileType, Disposition
import time
import os
import base64
import traceback
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# import cv2
import numpy as np
from qreader import QReader

# import os
import cv2
import base64


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

class QRCodeProcessor:
    @staticmethod
    def find_and_crop_qr_code(image_path, margin_ratio=0.1):
        # Load the image and convert from BGR to RGB
        image = cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB)
        qreader = QReader()
        detections, decoded_texts = qreader.detect_and_decode(image=image, return_detections=True)

        if not decoded_texts:
            print("No QR code found.")
            return None

        for url, details in zip(detections, decoded_texts):
            if details and 'bbox_xyxy' in details:
                # Ensure bounding box coordinates are integers
                bbox = [int(coord) for coord in details['bbox_xyxy']]
                x1, y1, x2, y2 = bbox
                width = x2 - x1
                height = y2 - y1

                # Calculate margin size
                margin_width = int(width * margin_ratio)
                margin_height = int(height * margin_ratio)

                # Apply margin, ensuring we do not go out of image bounds
                x1 = max(0, x1 - margin_width)
                y1 = max(0, y1 - margin_height)
                x2 = min(image.shape[1], x2 + margin_width)
                y2 = min(image.shape[0], y2 + margin_height)

                # Ensure final indices are integers
                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

                # Crop the image with margins
                cropped_image = image[y1:y2, x1:x2]
                cv2.imwrite("cropped_qr_code.jpg", cropped_image)
                return cv2.cvtColor(cropped_image, cv2.COLOR_RGB2BGR)  # Convert back to BGR for further processing

        print("QR code detected but not decodable.")
        return None

class SendMail:
    def __init__(
        self,
        sendgrid_api_key=os.environ.get("SENDGRID_API_KEY"),
        from_email=os.environ.get("FROM_EMAIL"),
        to_email=os.environ.get("TO_EMAIL"),
        app_password=os.environ.get("APP_PASSWORD"),
        smtp_server="smtp.gmail.com",
        smtp_port=587,
    ):
        self.from_email = from_email
        self.to_email = to_email
        self.app_password = app_password or sendgrid_api_key
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    def send_email(self, subject, content, attachment_path, attachment_name):
        if not self.from_email or not self.to_email or not self.app_password:
            print("SMTP not configured. Skipping email send.")
            return False

        msg = MIMEMultipart("mixed")
        msg["From"] = self.from_email
        msg["To"] = self.to_email
        msg["Subject"] = subject

        body = MIMEMultipart("alternative")
        body.attach(MIMEText(content, "plain"))

        cropped_image = QRCodeProcessor.find_and_crop_qr_code(attachment_path)
        if cropped_image is not None:
            _, buffer = cv2.imencode(".png", cropped_image)
            encoded_cropped = base64.b64encode(buffer).decode()
            html_content = (
                f"<html><body><p>{content}</p>"
                f"<img src='data:image/png;base64,{encoded_cropped}' "
                f"alt='Cropped QR Code'></body></html>"
            )
            body.attach(MIMEText(html_content, "html"))

        msg.attach(body)

        try:
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={attachment_name}",
            )
            msg.attach(part)
        except Exception as exc:
            print(f"Warning: Could not attach file {attachment_path}: {exc}")

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.from_email, self.app_password)
            server.sendmail(self.from_email, self.to_email, msg.as_string())
            server.quit()
            print(f"Email sent successfully to {self.to_email}")
            return True
        except Exception as exc:
            print(f"Failed to send email via SMTP: {exc}")
            traceback.print_exc()
            return False


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
        traceback.print_exc()


def close_extra_tabs(driver):
    try:
        handles = driver.window_handles
    except Exception:
        return
    if not handles or len(handles) <= 1:
        return
    try:
        keep = driver.current_window_handle
    except Exception:
        keep = handles[0]
    for handle in handles:
        if handle == keep:
            continue
        try:
            driver.switch_to.window(handle)
            driver.close()
        except Exception:
            continue
    try:
        driver.switch_to.window(keep)
    except Exception:
        pass


def log_html_snapshot(driver, platform, label="error"):
    try:
        html = driver.page_source
    except Exception as exc:
        print(f"Failed to capture HTML for {platform}: {exc}")
        return None
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    safe_platform = str(platform).lower()
    log_path = os.path.join(logs_dir, f"selenium-{safe_platform}.log")
    try:
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write(f"\n===== {timestamp} {label} =====\n")
            handle.write(html)
            handle.write("\n===== END =====\n")
        print(f"Saved HTML snapshot to {log_path}")
        return log_path
    except Exception as exc:
        print(f"Failed to write HTML snapshot for {platform}: {exc}")
        return None
