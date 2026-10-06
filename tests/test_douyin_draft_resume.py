import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


utils = types.ModuleType("utils")
for name in ("dismiss_alert", "bring_to_front", "close_extra_tabs", "safe_get"):
    setattr(utils, name, Mock())
login = types.ModuleType("login_douyin")
login.DouyinLogin = Mock()
spec = importlib.util.spec_from_file_location("douyin_under_test", Path(__file__).resolve().parents[1] / "pub_douyin.py")
module = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {"utils": utils, "login_douyin": login}):
    spec.loader.exec_module(module)


class DraftResumeTests(unittest.TestCase):
    def make_publisher(self, states):
        p = module.DouyinPublisher.__new__(module.DouyinPublisher)
        p.driver = Mock()
        p.driver.execute_script.side_effect = states
        p._body_text = Mock(return_value="你还有上次未发布的视频")
        p._safe_click = Mock(return_value=True)
        p._save_upload_debug_snapshot = Mock(return_value=("debug/draft", {}))
        return p

    def test_already_entered_editor_does_not_wait_for_vanished_button(self):
        p = self.make_publisher([{"editor": True, "prompt": False}])
        self.assertTrue(p._resume_unpublished_draft_if_present(for_replacement=True))
        p._safe_click.assert_not_called()

    def test_continue_is_clicked_once_then_route_is_confirmed(self):
        button = Mock()
        p = self.make_publisher([
            {"editor": False, "prompt": True, "button": button},
            {"editor": True, "prompt": False},
        ])
        with patch.object(module.time, "sleep"):
            self.assertTrue(p._resume_unpublished_draft_if_present())
        p._safe_click.assert_called_once_with(button)

    def test_disappeared_prompt_on_upload_page_allows_fresh_upload(self):
        p = self.make_publisher([{"editor": False, "prompt": False}])
        self.assertFalse(p._resume_unpublished_draft_if_present())

    def test_persistent_unusable_modal_saves_evidence_and_stops(self):
        p = self.make_publisher([{"editor": False, "prompt": True}])
        with patch.object(module.time, "monotonic", side_effect=[0, 1, 13]), patch.object(module.time, "sleep"):
            with self.assertRaisesRegex(module.UploadInputMissingException, "debug/draft"):
                p._resume_unpublished_draft_if_present()
        p._save_upload_debug_snapshot.assert_called_once_with("draft_resume_timeout")


if __name__ == "__main__":
    unittest.main()
