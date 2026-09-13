import json
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import instagram_caption_input as caption_input
from instagram_caption_input import (
    InstagramCaptionError, editor_has_caption, rendered_caption_matches,
)

utils_stub = types.ModuleType("utils")
for name in ("dismiss_alert", "bring_to_front", "close_extra_tabs"):
    setattr(utils_stub, name, lambda *args: None)
login_stub = types.ModuleType("login_instagram")
login_stub.InstagramLogin = MagicMock()
with patch.dict(sys.modules, {"utils": utils_stub, "login_instagram": login_stub}):
    import pub_instagram


class CaptionPersistenceTests(unittest.TestCase):
    def test_dom_text_with_empty_lexical_state_is_rejected(self):
        self.assertFalse(editor_has_caption({"text": "Caption", "lexical": True, "counter": 0}, "Caption"))

    def test_lexical_counter_and_complete_text_must_match(self):
        good = {"text": "JP\nEN\nZH", "lexical": True, "counter": 8}
        self.assertTrue(editor_has_caption(good, "JP\nEN\nZH"))
        self.assertFalse(editor_has_caption({**good, "text": "JP"}, "JP\nEN\nZH"))
        self.assertFalse(editor_has_caption({**good, "counter": None}, "JP\nEN\nZH"))

    def test_counter_uses_browser_utf16_length(self):
        self.assertTrue(editor_has_caption({"text": "\U0001f600", "lexical": True, "counter": 2}, "\U0001f600"))

    def test_legacy_textarea_does_not_require_lexical_counter(self):
        self.assertTrue(editor_has_caption({"text": "Caption", "lexical": False}, "Caption"))

    def test_saved_caption_requires_all_languages_not_only_title(self):
        expected = "Title\nJP\nEN\nZH"
        self.assertFalse(rendered_caption_matches("Title", expected))
        self.assertFalse(rendered_caption_matches("", expected))
        self.assertFalse(rendered_caption_matches("", ""))
        self.assertTrue(rendered_caption_matches("Title JP EN ZH", expected))

    def test_empty_caption_is_blocked_before_editor_or_share(self):
        driver = MagicMock()
        with self.assertRaises(InstagramCaptionError):
            caption_input.enter_verified_caption(driver, MagicMock(), " ")
        driver.execute_script.assert_not_called()

    def test_native_input_replaces_then_blurs_and_verifies(self):
        driver, editor, finder = MagicMock(), MagicMock(), MagicMock()
        with patch.object(caption_input, "WebDriverWait") as wait, patch.object(
            caption_input, "verify_editor_caption"
        ) as verify:
            wait.return_value.until.return_value = editor
            caption_input.enter_verified_caption(driver, finder, "New caption")
            self.assertEqual([call.args for call in editor.send_keys.call_args_list], [
                (caption_input.Keys.CONTROL, "a"), ("New caption",), (caption_input.Keys.TAB,),
            ])
            verify.assert_called_once_with(driver, finder, "New caption")
            self.assertNotIn("execCommand", driver.execute_script.call_args.args[0])

    def test_uncommitted_text_blocks_submission(self):
        with patch.object(caption_input, "WebDriverWait") as wait:
            wait.return_value.until.side_effect = TimeoutError("counter stayed zero")
            with self.assertRaises(InstagramCaptionError):
                caption_input.verify_editor_caption(MagicMock(), MagicMock(), "Caption")

    def test_keyboard_failure_preserves_existing_upload(self):
        with patch.object(caption_input, "WebDriverWait") as wait:
            wait.return_value.until.return_value.send_keys.side_effect = RuntimeError("input interrupted")
            with self.assertRaises(InstagramCaptionError):
                caption_input.enter_verified_caption(MagicMock(), MagicMock(), "Caption")

    def test_hidden_editor_is_not_an_input_fallback(self):
        driver, hidden = MagicMock(), MagicMock()
        hidden.is_displayed.return_value = False
        driver.find_elements.return_value = [hidden]
        self.assertFalse(pub_instagram.InstagramPublisher._find_caption_editor(driver))


class PublisherCaptionTests(unittest.TestCase):
    def make_publisher(self):
        publisher = pub_instagram.InstagramPublisher.__new__(pub_instagram.InstagramPublisher)
        publisher.driver = MagicMock()
        publisher.metadata = {"title": "JP EN ZH"}
        publisher.published_post_url = None
        return publisher

    def test_profile_verification_requires_saved_caption(self):
        publisher = self.make_publisher()
        publisher.driver.find_elements.return_value = [MagicMock()]
        publisher.driver.find_elements.return_value[0].get_attribute.side_effect = [
            "https://www.instagram.com/example/", "https://www.instagram.com/example/reel/test/",
        ]
        class Wait:
            def __init__(self, driver, timeout):
                self.driver = driver
            def until(self, condition):
                value = condition(self.driver)
                if not value:
                    raise TimeoutError("caption absent")
                return value
        with patch.object(pub_instagram, "WebDriverWait", Wait):
            publisher.driver.execute_script.return_value = ["JP only"]
            self.assertFalse(publisher._verify_latest_profile_post(timeout=1))
        self.assertEqual(publisher.published_post_url, "https://www.instagram.com/example/reel/test/")

    def test_complete_saved_span_caption_is_accepted(self):
        publisher = self.make_publisher()
        publisher.driver.find_elements.return_value = [MagicMock()]
        publisher.driver.find_elements.return_value[0].get_attribute.side_effect = [
            "https://www.instagram.com/example/", "https://www.instagram.com/example/reel/test/",
        ]
        publisher.driver.execute_script.return_value = ["JP EN ZH"]
        with patch.object(pub_instagram, "WebDriverWait") as wait:
            wait.return_value.until.side_effect = lambda predicate: predicate(publisher.driver)
            self.assertTrue(publisher._verify_latest_profile_post(timeout=1))
        self.assertIn("main span", publisher.driver.execute_script.call_args.args[0])

    def test_shared_receipt_without_saved_caption_is_not_success(self):
        publisher = self.make_publisher()
        publisher.retry_count = 0
        with patch.object(pub_instagram.time, "sleep"), patch.object(
            pub_instagram, "WebDriverWait"
        ), patch.object(pub_instagram, "fit_browser_window"), patch.object(
            pub_instagram, "enter_verified_caption"
        ), patch.object(pub_instagram, "verify_editor_caption"), patch.object(
            publisher, "_find_first", return_value=MagicMock()
        ), patch.object(publisher, "_upload_dialog_present", return_value=True), patch.object(
            publisher, "_upload_video"
        ) as upload, patch.object(publisher, "_dismiss_reels_dialog"), patch.object(
            publisher, "_wait_for_crop_original", return_value=True
        ), patch.object(publisher, "_click_next_until_caption"), patch.object(
            publisher, "_click_share_button"
        ) as share, patch.object(publisher, "_wait_for_publish_complete", return_value=True), patch.object(
            publisher, "_verify_latest_profile_post", return_value=False
        ) as verify, patch.object(publisher, "_log_category_routing"):
            with self.assertRaises(InstagramCaptionError):
                publisher.publish()
            share.assert_called_once()
            verify.assert_called_once()
            upload.assert_called_once()


class ExportTests(unittest.TestCase):
    def test_export_reuses_builder_and_preserves_different_existing_file(self):
        script = Path(__file__).resolve().parents[1] / "scripts/export_instagram_caption.py"
        with tempfile.TemporaryDirectory() as folder:
            meta, output = Path(folder) / "meta.json", Path(folder) / "caption.txt"
            meta.write_text(json.dumps({"title": "ZH", "japanese_version": {"title": "JP"}, "english_version": {"title": "EN"}}))
            result = subprocess.run([sys.executable, str(script), str(meta), str(output)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_text(), "JP\n\nEN\n\nZH\n")
            output.write_text("Preserve this older version")
            result = subprocess.run([sys.executable, str(script), str(meta), str(output)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_text(), "Preserve this older version")


if __name__ == "__main__":
    unittest.main()
