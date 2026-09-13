import ast
import unittest
from pathlib import Path
from types import SimpleNamespace

from browser_window import fit_browser_window
from douyin_submit import submit_outcome


class SubmitEvidenceTests(unittest.TestCase):
    def test_navigation_and_status_filters_are_not_success(self):
        self.assertEqual(submit_outcome("/creator-micro/content/upload", "内容管理\n作品管理\n审核中\n已提交"), "pending")

    def test_upload_failure_wins_over_navigation(self):
        self.assertEqual(submit_outcome("/creator-micro/content/upload", "内容管理\n上传失败，重新上传"), "blocked")

    def test_explicit_receipt_is_accepted(self):
        self.assertEqual(submit_outcome("/creator-micro/content/upload", "内容管理\n发布成功"), "accepted")

    def test_static_success_help_is_not_a_receipt(self):
        self.assertEqual(submit_outcome("/creator-micro/content/upload", "发布成功后可编辑作品"), "pending")

    def test_management_navigation(self):
        self.assertEqual(submit_outcome("https://creator.douyin.com/creator-micro/content/manage?from=publish", "作品列表"), "accepted")


class DesktopBoundsTests(unittest.TestCase):
    def test_small_desktop_and_panel_offset(self):
        calls = []
        actual = dict(x=0, y=64, width=1024, height=704)
        driver = SimpleNamespace(
            execute_script=lambda script: dict(x=0, y=36, width=1024, height=732),
            maximize_window=lambda: calls.append("maximize"),
            get_window_rect=lambda: actual,
        )
        self.assertEqual(fit_browser_window(driver), actual)
        self.assertEqual(len(calls), 1)
        self.assertEqual(actual["y"] + actual["height"], 768)

    def test_invalid_bounds_do_not_resize(self):
        driver = SimpleNamespace(execute_script=lambda script: dict(x=0, y=0, width=0, height=0), maximize_window=lambda: self.fail("unexpected resize"))
        with self.assertRaises(ValueError):
            fit_browser_window(driver)


class InstagramLabelsTests(unittest.TestCase):
    def test_old_and_new_caption_labels_share_selector_set(self):
        # Load UI constants without importing desktop/login side effects.
        tree = ast.parse(Path(__file__).with_name("pub_instagram.py").read_text())
        nodes = [node for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in {"CAPTION_LABELS", "CAPTION_SELECTORS"} for t in node.targets)]
        scope = {}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), "caption-selectors", "exec"), scope)
        for label in ("Write a caption...", "Add a caption..."):
            self.assertTrue(any(label in selector and "contenteditable" in selector for selector in scope["CAPTION_SELECTORS"]))
            self.assertTrue(any(label in selector and "textarea" in selector for selector in scope["CAPTION_SELECTORS"]))


if __name__ == "__main__":
    unittest.main()
