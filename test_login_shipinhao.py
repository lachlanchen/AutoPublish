import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

utils_stub = types.ModuleType("utils")
utils_stub.QRCodeProcessor = MagicMock()
utils_stub.SendMail = MagicMock()
utils_stub.dismiss_alert = MagicMock()
utils_stub.bring_to_front = MagicMock()
utils_stub.log_html_snapshot = MagicMock()
sys.modules["utils"] = utils_stub

from login_shipinhao import ShiPinHaoLogin


def element(*, visible=False, text="", src=""):
    item = MagicMock()
    item.is_displayed.return_value = visible
    item.text = text
    item.get_attribute.side_effect = lambda name: src if name == "src" else ""
    return item


class ShipinhaoQrExpiryTests(unittest.TestCase):
    def setUp(self):
        self.login = ShiPinHaoLogin.__new__(ShiPinHaoLogin)
        self.login.driver = MagicMock()

    def test_new_wechat_visible_refresh_button_means_expired(self):
        refresh = element(visible=True)

        def find_elements(_by, selector):
            if selector == ".js_refresh_qrcode":
                return [refresh]
            return []

        self.login.driver.find_elements.side_effect = find_elements
        self.assertTrue(self.login._current_context_has_outdated_qr())

    def test_hidden_refresh_button_does_not_mean_expired(self):
        refresh = element(visible=False)

        def find_elements(_by, selector):
            if selector == ".js_refresh_qrcode":
                return [refresh]
            return []

        self.login.driver.find_elements.side_effect = find_elements
        self.assertFalse(self.login._current_context_has_outdated_qr())

    def test_legacy_visible_expiry_text_remains_supported(self):
        expiry_tip = element(visible=True, text="二维码已过期，点击刷新")

        def find_elements(_by, selector):
            if selector == ".mask.show .refresh-tip":
                return [expiry_tip]
            return []

        self.login.driver.find_elements.side_effect = find_elements
        self.assertTrue(self.login._current_context_has_outdated_qr())

    def test_login_wait_uses_shared_environment_setting(self):
        with patch.dict(os.environ, {"AUTOPUBLISH_LOGIN_WAIT_SECONDS": "7200"}):
            self.assertEqual(self.login._login_wait_seconds(), 7200)

    def test_email_uses_direct_watch_qr_artifact(self):
        self.login.mailer = MagicMock()
        self.login._notify_attention = MagicMock()
        self.login._save_visible_qr_screenshot = MagicMock(return_value="/tmp/qr-source.png")
        utils_stub.QRCodeProcessor.build_watch_friendly_png.return_value = "/tmp/watch-qr.png"

        self.login.take_screenshot_and_send_email()

        self.login._notify_attention.assert_called_once_with("required", "/tmp/watch-qr.png")
        self.login.mailer.send_email.assert_called_once_with(
            "Shipinhao Login Required",
            "Login is required. Please scan the attached QR code.",
            "/tmp/watch-qr.png",
            "shipinhao-login-qr.png",
        )


if __name__ == "__main__":
    unittest.main()
