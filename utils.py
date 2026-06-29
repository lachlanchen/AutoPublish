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
import tempfile
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from html import escape
from urllib.parse import urlsplit

from PIL import Image, UnidentifiedImageError

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
        source_image = cv2.imread(image_path)
        if source_image is None:
            print(f"Could not read QR source image: {image_path}")
            return None

        image = cv2.cvtColor(source_image, cv2.COLOR_BGR2RGB)
        qreader = QReader()
        try:
            first, second = qreader.detect_and_decode(image=image, return_detections=True)
        except Exception as exc:
            print(f"QR detection failed: {exc}")
            return None

        if first and isinstance(first[0], dict):
            detections, decoded_texts = first, second
        else:
            decoded_texts, detections = first, second

        if not detections:
            print("No QR code found.")
            return None

        for details, decoded_text in zip(detections, decoded_texts):
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
                return cv2.cvtColor(cropped_image, cv2.COLOR_RGB2BGR)  # Convert back to BGR for further processing

        print("QR code detected but not decodable.")
        return None

    @staticmethod
    def build_watch_friendly_png(source_path, output_path=None, image_size=248, canvas_size=320):
        """Create a high-contrast QR PNG that renders reliably in Apple Watch Mail."""
        if output_path is None:
            output_path = os.path.join(tempfile.gettempdir(), f"autopub-login-qr-{uuid.uuid4().hex}.png")

        crop = QRCodeProcessor.find_and_crop_qr_code(source_path)
        if crop is not None:
            image = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
        else:
            image = Image.open(source_path)

        image = image.convert("L")
        image = image.point(lambda pixel: 0 if pixel < 165 else 255, mode="1").convert("L")
        resampling = getattr(Image, "Resampling", Image)
        image = image.resize((image_size, image_size), resampling.NEAREST)

        canvas = Image.new("L", (canvas_size, canvas_size), 255)
        offset = ((canvas_size - image_size) // 2, (canvas_size - image_size) // 2)
        canvas.paste(image, offset)
        canvas.save(output_path, format="PNG", optimize=False)
        return output_path

class SendMail:
    def __init__(
        self,
        sendgrid_api_key=None,
        from_email=None,
        to_email=None,
        app_password=None,
        smtp_server="smtp.gmail.com",
        smtp_port=587,
    ):
        self.from_email = from_email or os.environ.get("FROM_EMAIL")
        self.to_email = to_email or os.environ.get("TO_EMAIL")
        legacy_password = None
        if sendgrid_api_key and not str(sendgrid_api_key).startswith("SG."):
            legacy_password = sendgrid_api_key
        self.app_password = app_password or os.environ.get("APP_PASSWORD") or legacy_password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    def send_email(self, subject, content, attachment_path, attachment_name):
        if not self.from_email or not self.to_email or not self.app_password:
            print("SMTP not configured. Missing FROM_EMAIL, TO_EMAIL, or APP_PASSWORD.")
            return False

        msg = MIMEMultipart("related")
        msg["From"] = self.from_email
        msg["To"] = self.to_email
        msg["Subject"] = subject

        body = MIMEMultipart("alternative")
        body.attach(MIMEText(content, "plain"))
        qr_cid = f"autopub-login-qr-{uuid.uuid4().hex}"
        qr_png_path = None
        try:
            qr_png_path = QRCodeProcessor.build_watch_friendly_png(attachment_path)
            html_content = (
                "<html><body>"
                f"<p>{escape(content).replace(chr(10), '<br>')}</p>"
                f"<img src=\"cid:{qr_cid}\" alt=\"Login QR code\" width=\"320\" height=\"320\" "
                "style=\"display:block;width:320px;height:320px;border:0;outline:0;\">"
                "</body></html>"
            )
            body.attach(MIMEText(html_content, "html"))
        except (OSError, UnidentifiedImageError, cv2.error) as exc:
            print(f"Warning: Could not prepare watch-friendly QR image: {exc}")

        msg.attach(body)

        if qr_png_path:
            try:
                with open(qr_png_path, "rb") as qr_file:
                    qr_part = MIMEImage(qr_file.read(), _subtype="png")
                qr_part.add_header("Content-ID", f"<{qr_cid}>")
                qr_part.add_header("Content-Disposition", "inline", filename="autopub-login-qr.png")
                msg.attach(qr_part)
            except Exception as exc:
                print(f"Warning: Could not attach inline QR image {qr_png_path}: {exc}")

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


def safe_get(driver, url, timeout=45, label=None):
    label = label or url
    target = urlsplit(url)
    target_path = target.path.rstrip("/")

    def _current_url():
        try:
            return driver.current_url or ""
        except Exception:
            return ""

    def _url_matches_target():
        current = urlsplit(_current_url())
        current_path = current.path.rstrip("/")
        return (
            current.netloc == target.netloc
            and (not target_path or current_path == target_path or current_path.startswith(target_path))
        )

    def _has_body():
        try:
            return bool(driver.execute_script("return !!document.body;"))
        except Exception:
            return False

    def _matches_target():
        return _url_matches_target() and _has_body()

    try:
        driver.set_page_load_timeout(min(timeout, 10))
    except Exception:
        pass
    try:
        driver.set_script_timeout(3)
    except Exception:
        pass

    if _matches_target():
        print(f"Already on {label}: {driver.current_url}")
        return True

    try:
        driver.get(url)
        if _matches_target():
            print(f"Navigated to {label}: {driver.current_url}")
            return True
    except Exception as exc:
        print(f"Timed out or failed while navigating to {label}: {exc}")

    start_time = time.time()
    while time.time() - start_time <= min(timeout, 5):
        if _matches_target():
            print(f"Using partially loaded {label}: {driver.current_url}")
            return True
        time.sleep(0.5)

    print(f"Continuing after bounded navigation attempt for {label}: {_current_url()}")
    return False


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
        if not os.environ.get("DISPLAY"):
            os.environ["DISPLAY"] = ":1" if os.path.exists("/tmp/.X11-unix/X1") else ":0"
        search_commands = [
            ["xdotool", "search", "--onlyvisible", "--name", "Chromium"],
            ["xdotool", "search", "--name", "Chromium"],
            ["xdotool", "search", "--onlyvisible", "--class", "chromium"],
            ["xdotool", "search", "--class", "chromium"],
        ]
        window_list = []
        last_error = ""
        for command in search_commands:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.stdout.strip():
                window_list = result.stdout.strip().splitlines()
                break
            last_error = (result.stderr or "").strip()
        if not window_list:
            print(f"No Chromium windows found by xdotool. {last_error}")
            return
        # Iterate through the list of window IDs
        for window_id in window_list:
            # Get the name of each window using its ID
            try:
                result = subprocess.run(
                    ["xdotool", "getwindowname", window_id],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    check=False,
                )
                if result.returncode != 0:
                    continue
                window_name = result.stdout.strip()
            except Exception:
                continue
            # Check if the window name matches any of the patterns provided
            if any(text in window_name for text in window_name_pattern):
                # If a match is found, activate the window
                subprocess.run(
                    ["xdotool", "windowactivate", "--sync", window_id],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                # Optionally, add a brief pause to ensure the window comes to the front
                subprocess.run(["sleep", "1"])
                break  # Exit the loop after the first match
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.output.decode()}")
    except Exception as e:
        print(f"Could not bring browser window to front: {e}")


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
