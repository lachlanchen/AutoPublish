import smtplib
import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

class SendMail:
    def __init__(self, sendgrid_api_key=None, from_email=None, to_email=None):
        # Use environment variables with fallbacks
        self.from_email = from_email or os.environ.get('FROM_EMAIL')
        self.to_email = to_email or os.environ.get('TO_EMAIL')
        
        # For password, try APP_PASSWORD first, then fallback to SENDGRID_API_KEY
        self.app_password = (sendgrid_api_key or 
                           os.environ.get('APP_PASSWORD') or 
                           os.environ.get('SENDGRID_API_KEY'))
        
        # SMTP settings
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587

    def send_email(self, subject, content, attachment_path, attachment_name):
        """
        Send email with attachment - compatible with original SendMail interface
        """
        try:
            # Create message
            msg = MIMEMultipart('mixed')
            msg['From'] = self.from_email
            msg['To'] = self.to_email
            msg['Subject'] = subject
            
            # Create the body container
            body = MIMEMultipart('alternative')
            
            # Add plain text content
            text_part = MIMEText(content, 'plain')
            body.attach(text_part)
            
            # Try QR processing if modules are available, otherwise skip
            html_content_added = False
            try:
                # Only import if needed and available
                import cv2
                import numpy as np
                from qreader import QReader
                
                print("QR processing libraries available, processing QR code...")
                # Process QR code (your original logic)
                cropped_image = self._find_and_crop_qr_code(attachment_path)
                if cropped_image is not None:
                    _, buffer = cv2.imencode('.png', cropped_image)
                    encoded_cropped = base64.b64encode(buffer).decode()
                    img_html = f"<img src='data:image/png;base64,{encoded_cropped}' alt='Cropped QR Code' style='max-width:500px;'>"
                    html_content = f"<html><body><p>{content}</p><br>{img_html}</body></html>"
                    html_part = MIMEText(html_content, 'html')
                    body.attach(html_part)
                    html_content_added = True
                    print("QR code processed and embedded in HTML")
                    
            except ImportError as e:
                print(f"QR processing libraries not available: {e}")
                print("Continuing without QR code processing...")
            except Exception as e:
                print(f"QR processing failed: {e}")
                print("Continuing without QR code processing...")
            
            # Add body to main message
            msg.attach(body)
            
            # Attach the original image
            try:
                with open(attachment_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment_name}',
                )
                msg.attach(part)
                print(f"Attached file: {attachment_name}")
                
            except Exception as e:
                print(f"Warning: Could not attach file {attachment_path}: {e}")
            
            # Connect to server and send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.from_email, self.app_password)
            
            text = msg.as_string()
            server.sendmail(self.from_email, self.to_email, text)
            server.quit()
            
            print(f"Email sent successfully to {self.to_email}!")
            
        except Exception as e:
            print(f"Error sending email: {e}")
            import traceback
            traceback.print_exc()

    def _find_and_crop_qr_code(self, image_path, margin_ratio=0.1):
        """QR code processing - only called if libraries are available"""
        import cv2
        import numpy as np
        from qreader import QReader
        
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

# Base SendMail class for general email sending (no QR processing)
class SendMailBase:
    def __init__(self, from_email=None, to_email=None, app_password=None, 
                 smtp_server='smtp.gmail.com', smtp_port=587):
        self.from_email = from_email or os.environ.get('FROM_EMAIL')
        self.to_email = to_email or os.environ.get('TO_EMAIL')
        self.app_password = app_password or os.environ.get('APP_PASSWORD')
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    def send_simple_email(self, subject, content, to_email=None):
        """Send simple text email"""
        recipient = to_email or self.to_email
        try:
            msg = MIMEText(content)
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = recipient
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.from_email, self.app_password)
            server.sendmail(self.from_email, recipient, msg.as_string())
            server.quit()
            
            print(f"Simple email sent to {recipient}")
            
        except Exception as e:
            print(f"Error sending simple email: {e}")

    def send_email_with_attachment(self, subject, content, attachment_path, attachment_name, to_email=None):
        """Send email with single attachment"""
        recipient = to_email or self.to_email
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = recipient
            msg['Subject'] = subject
            
            # Add text content
            msg.attach(MIMEText(content, 'plain'))
            
            # Add attachment
            with open(attachment_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename= {attachment_name}')
            msg.attach(part)
            
            # Send
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.from_email, self.app_password)
            server.sendmail(self.from_email, recipient, msg.as_string())
            server.quit()
            
            print(f"Email with attachment sent to {recipient}")
            
        except Exception as e:
            print(f"Error sending email with attachment: {e}")

# Test the classes
if __name__ == "__main__":
    test_from_email = (
        os.environ.get("SMTP_TEST_FROM_EMAIL")
        or os.environ.get("FROM_EMAIL")
    )
    test_to_email = (
        os.environ.get("SMTP_TEST_TO_EMAIL")
        or os.environ.get("TO_EMAIL")
    )
    test_app_password = (
        os.environ.get("SMTP_TEST_APP_PASSWORD")
        or os.environ.get("APP_PASSWORD")
        or os.environ.get("SENDGRID_API_KEY")
    )

    if not (test_from_email and test_to_email and test_app_password):
        print(
            "Set SMTP_TEST_FROM_EMAIL, SMTP_TEST_TO_EMAIL, SMTP_TEST_APP_PASSWORD "
            "or the base FROM_EMAIL/TO_EMAIL/APP_PASSWORD to run the demo."
        )
    else:
        print("=== Testing SendMail Class (Original Compatible) ===")
        mailer = SendMail(
            sendgrid_api_key=test_app_password,
            from_email=test_from_email,
            to_email=test_to_email,
        )

        subject = "Test from Updated SendMail Class"
        content = "This is a test email from the updated SendMail class using SMTP instead of SendGrid."

        attachment_path = "cropped_qr_code.jpg"
        attachment_name = "qr_test.jpg"

        if os.path.exists(attachment_path):
            print(f"Sending email with attachment: {attachment_path}")
            mailer.send_email(subject, content, attachment_path, attachment_name)
        else:
            print(f"File not found: {attachment_path}")
            image_file = next(
                (f for f in os.listdir('.') if f.lower().endswith(('.png', '.jpg', '.jpeg'))),
                None,
            )
            if image_file:
                print(f"Using test file: {image_file}")
                mailer.send_email(subject, content, image_file, image_file)
            else:
                print("No image files found for testing")

        print("\n=== Testing SendMailBase Class (General Purpose) ===")
        base_mailer = SendMailBase(
            from_email=test_from_email,
            to_email=test_to_email,
            app_password=test_app_password,
        )
        base_mailer.send_simple_email("Test Simple Email", "This is a simple test email without attachments.")
        print("\n=== Test completed! ===")
        print("Set environment variables as explained above before rerunning the demo.")
