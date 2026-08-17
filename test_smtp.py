import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from smtp import SendMail


class SendMailResultTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.attachment = Path(self.temp_dir.name) / "qr.png"
        self.attachment.write_bytes(b"test")
        self.mailer = SendMail(
            sendgrid_api_key="test-password",
            from_email="sender@example.test",
            to_email="receiver@example.test",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("smtp.smtplib.SMTP")
    def test_send_email_returns_true_after_smtp_success(self, smtp_factory):
        smtp_factory.return_value = MagicMock()
        result = self.mailer.send_email(
            "subject",
            "content",
            str(self.attachment),
            "qr.png",
        )
        self.assertTrue(result)

    @patch("smtp.smtplib.SMTP", side_effect=OSError("offline"))
    def test_send_email_returns_false_after_smtp_failure(self, _smtp_factory):
        result = self.mailer.send_email(
            "subject",
            "content",
            str(self.attachment),
            "qr.png",
        )
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
