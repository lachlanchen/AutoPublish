import sys
import ast
from pathlib import Path
import shutil
import subprocess
import types
import unittest
from contextlib import ExitStack
from unittest.mock import MagicMock, patch

from youtube_checks import checks_outcome


utils_stub = types.ModuleType("utils")
for name in ("dismiss_alert", "bring_to_front", "close_extra_tabs"):
    setattr(utils_stub, name, lambda *args: None)
with patch.dict(sys.modules, {"utils": utils_stub}):
    import pub_y2b


class CheckStatusTests(unittest.TestCase):
    def test_ready_next_and_video_link_are_not_completed_checks(self):
        self.assertEqual(checks_outcome("Upload complete", "Video link\nNext"), "pending")

    def test_one_completed_subcheck_does_not_complete_every_check(self):
        self.assertEqual(checks_outcome("Checking", "Community Guidelines\nNo issues found"), "pending")

    def test_complete_without_issues(self):
        self.assertEqual(checks_outcome("Checks complete. No issues found."), "complete")

    def test_warning_wins_over_stale_complete_footer(self):
        self.assertEqual(checks_outcome("Checks complete. No issues found.", warning=True), "pending")

    def test_claim_requires_explicit_nonrestricting_details(self):
        progress = "Checks complete. Claimed content found."
        self.assertEqual(checks_outcome(progress), "review")
        self.assertEqual(checks_outcome(progress, "This claim doesn’t affect your video’s visibility or features"), "complete")
        self.assertEqual(checks_outcome(progress, "Blocked in some countries"), "review")

    def test_unknown_result_is_not_accepted(self):
        self.assertEqual(checks_outcome("Checks complete. New policy notice."), "review")


class PublishFlowTests(unittest.TestCase):
    def setUp(self):
        self.driver = MagicMock()
        self.publisher = pub_y2b.YouTubePublisher(self.driver, "video.mp4", "cover.jpg", {"title": "Reviewed title"})

    def test_wait_polls_until_actual_completion(self):
        with patch.object(self.publisher, "_check_snapshot", side_effect=[
            {"progress": "Checking", "details": "No issues found\nNext"},
            {"progress": "Checks complete. No issues found."},
        ]) as snapshot, patch.object(pub_y2b.time, "sleep"):
            self.assertTrue(self.publisher.wait_for_checks())
            self.assertEqual(snapshot.call_count, 2)

    @unittest.skipUnless(shutil.which("node"), "Node is required to validate embedded JavaScript")
    def test_embedded_javascript_is_syntactically_valid(self):
        tree = ast.parse(Path(pub_y2b.__file__).read_text())
        checked = 0
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "execute_script" and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)):
                continue
            result = subprocess.run(
                ["node", "--check"],
                input="function seleniumScript() {\n" + node.args[0].value + "\n}",
                text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, f"line {node.lineno}: {result.stderr}")
            checked += 1
        self.assertGreater(checked, 5)

    def test_matching_draft_is_resumed_without_upload_navigation(self):
        self.driver.execute_script.return_value = {"open": True, "matches": True}
        with patch.object(pub_y2b, "WebDriverWait"):
            self.publisher.upload_video()
        self.driver.get.assert_not_called()
        self.assertTrue(self.publisher._upload_started)

    def test_different_draft_is_preserved(self):
        self.driver.execute_script.return_value = {"open": True, "matches": False}
        with self.assertRaises(pub_y2b.YouTubePublishPendingException):
            self.publisher.upload_video()
        self.driver.get.assert_not_called()

    def test_success_overlay_is_closed_before_draft_guard(self):
        self.driver.execute_script.side_effect = [
            {"completed": True, "closed": True}, {"open": False},
        ]
        with patch.object(pub_y2b, "WebDriverWait"):
            self.assertFalse(self.publisher._resume_matching_open_upload())
        self.assertIn("ytcp-video-share-dialog", self.driver.execute_script.call_args_list[0].args[0])

    def test_receipt_without_safe_close_blocks_new_upload(self):
        self.driver.execute_script.return_value = {"completed": True, "closed": False}
        with self.assertRaises(pub_y2b.YouTubePublishPendingException):
            self.publisher.upload_video()
        self.driver.get.assert_not_called()

    def test_delayed_receipt_close_must_finish_before_new_upload(self):
        self.driver.execute_script.return_value = {"completed": True, "closed": True}
        with patch.object(pub_y2b, "WebDriverWait") as wait:
            wait.return_value.until.side_effect = pub_y2b.TimeoutException()
            with self.assertRaises(pub_y2b.YouTubePublishPendingException):
                self.publisher.upload_video()
        self.driver.get.assert_not_called()

    def test_cleanup_failure_does_not_fail_verified_publication(self):
        with ExitStack() as stack:
            for name in ("upload_video", "wait_for_processing", "set_video_details",
                         "set_thumbnail", "set_playlist", "set_not_for_kids",
                         "set_tags_and_more", "set_visibility_and_publish",
                         "verify_published_in_studio"):
                stack.enter_context(patch.object(self.publisher, name, return_value=True))
            stack.enter_context(patch.object(pub_y2b.time, "sleep"))
            stack.enter_context(patch.object(
                self.publisher, "_close_completed_publication",
                side_effect=pub_y2b.YouTubePublishPendingException("still closing"),
            ))
            self.assertTrue(self.publisher.publish())
            self.publisher.upload_video.assert_called_once()

    def test_timeout_keeps_upload_pending(self):
        with self.assertRaises(pub_y2b.YouTubePublishPendingException):
            self.publisher.wait_for_checks(duration=0)

    def test_warning_goes_back_instead_of_publish_anyway(self):
        with patch.object(self.publisher, "_published_dialog_result", return_value=None), patch.object(
            self.publisher, "_check_snapshot", return_value={"warning": True}
        ), patch.object(self.publisher, "_return_from_check_warning") as back:
            self.assertFalse(self.publisher._wait_for_publish_receipt())
            back.assert_called_once()

    def test_draft_title_cannot_pass_verification(self):
        self.driver.execute_script.return_value = ""
        with self.assertRaises(pub_y2b.YouTubePublishPendingException):
            self.publisher.verify_published_in_studio()
        self.assertIn("ytcp-video-share-dialog", self.driver.execute_script.call_args.args[0])

    def test_visible_receipt_is_accepted(self):
        self.driver.execute_script.return_value = "Video published\nReviewed title\nhttps://youtube.com/shorts/ABCdef12345"
        self.assertTrue(self.publisher.verify_published_in_studio())

    def test_stale_receipt_for_another_video_is_not_accepted(self):
        self.driver.execute_script.return_value = "Video published\nAnother title\nhttps://youtube.com/shorts/ABCdef12345"
        with self.assertRaises(pub_y2b.YouTubePublishPendingException):
            self.publisher.verify_published_in_studio()

    def test_failure_after_attachment_never_reuploads(self):
        def attach_then_fail():
            self.publisher._upload_started = True
            raise RuntimeError("connection interrupted after attachment")
        with patch.object(self.publisher, "upload_video", side_effect=attach_then_fail) as upload:
            with self.assertRaises(pub_y2b.YouTubePublishPendingException):
                self.publisher.publish()
            upload.assert_called_once()

    def test_warning_retry_reuses_existing_upload_and_rechecks(self):
        with patch.object(pub_y2b, "WebDriverWait") as wait, patch.object(pub_y2b.time, "sleep"), patch.object(
            self.publisher, "wait_for_checks"
        ) as checks, patch.object(self.publisher, "_wait_for_publish_receipt", side_effect=[False, True]), patch.object(
            self.publisher, "upload_video"
        ) as upload:
            self.assertTrue(self.publisher.set_visibility_and_publish())
            self.assertEqual(checks.call_count, 2)
            upload.assert_not_called()
            self.assertGreater(wait.call_count, 0)


if __name__ == "__main__":
    unittest.main()
