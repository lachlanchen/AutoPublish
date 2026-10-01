import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

utils_stub = types.ModuleType('utils')
utils_stub.safe_get = Mock()
spec = importlib.util.spec_from_file_location('verification_under_test', Path(__file__).resolve().parents[1] / 'publish_verification.py')
verification = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {'utils': utils_stub}):
    spec.loader.exec_module(verification)


class ManagementRefreshTests(unittest.TestCase):
    def test_stale_douyin_listing_refreshes_without_resubmission(self):
        driver = Mock()
        title = '牛肉配土豆 看著很好吃'
        with patch.object(verification.time, 'sleep'), \
             patch.object(verification, 'collect_page_text', side_effect=['old listing', title]), \
             patch.object(verification, 'scroll_management_page'):
            self.assertTrue(verification.verify_publish_in_management(
                driver, 'https://creator.douyin.com/creator-micro/content/manage',
                {'title': title}, platform_name='Douyin', timeout=10, scrolls_per_pass=1,
            ))
        driver.refresh.assert_called_once()
        self.assertEqual(driver.method_calls, [('refresh', (), {})])

    def test_current_listing_needs_no_refresh(self):
        driver = Mock()
        title = '牛肉配土豆 看著很好吃'
        with patch.object(verification.time, 'sleep'), \
             patch.object(verification, 'collect_page_text', return_value=title):
            self.assertTrue(verification.verify_publish_in_management(
                driver, 'https://creator.douyin.com/creator-micro/content/manage',
                {'title': title}, platform_name='Douyin', timeout=10,
            ))
        driver.refresh.assert_not_called()
