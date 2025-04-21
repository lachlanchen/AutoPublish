import cv2
import numpy as np
from qreader import QReader

import os
import cv2
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent, Attachment
from sendgrid.helpers.mail import FileContent, FileName, FileType, Disposition


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
    def __init__(self, sendgrid_api_key=os.environ.get('SENDGRID_API_KEY'), 
                 from_email=os.environ.get('FROM_EMAIL'), 
                 to_email=os.environ.get('TO_EMAIL')):
        self.sendgrid_api_key = sendgrid_api_key
        self.from_email = from_email
        self.to_email = to_email

    def send_email(self, subject, content, attachment_path, attachment_name):
        sg = SendGridAPIClient(self.sendgrid_api_key)
        mail = Mail(from_email=Email(self.from_email), to_emails=To(self.to_email), subject=subject)

        # Add plain text content
        mail.add_content(Content("text/plain", content))

        # Process the image to possibly crop the QR code with a margin
        cropped_image = QRCodeProcessor.find_and_crop_qr_code(attachment_path)
        if cropped_image is not None:
            _, buffer = cv2.imencode('.png', cropped_image)
            encoded_cropped = base64.b64encode(buffer).decode()
            html_content = f"<img src='data:image/png;base64,{encoded_cropped}' alt='Cropped QR Code'>"
            mail.add_content(HtmlContent(f"<html><body><p>{content}</p>{html_content}</body></html>"))

        # Attach the original image
        with open(attachment_path, 'rb') as f:
            data = f.read()
            encoded_file = base64.b64encode(data).decode()
        attachment = Attachment()
        attachment.file_content = FileContent(encoded_file)
        attachment.file_type = FileType('image/png')
        attachment.file_name = FileName(attachment_name)
        attachment.disposition = Disposition('attachment')
        mail.add_attachment(attachment)

        # Send the email
        response = sg.send(mail)
        print(f"Email sent, status code: {response.status_code}")

# Usage example
if __name__ == "__main__":
    mailer = SendMail()
    mailer.send_email(
        subject="Email with QR Code and Image Attachment",
        content="Find the QR code embedded below, and the original image attached.",
        attachment_path="test.png",
        attachment_name="original_image.png"
    )
