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


if __name__ == "__main__":
    unittest.main()
