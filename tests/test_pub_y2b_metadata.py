import sys
import types
import unittest
from unittest.mock import patch


utils_stub = types.ModuleType("utils")
utils_stub.dismiss_alert = lambda _driver: None
utils_stub.bring_to_front = lambda _titles: None
utils_stub.close_extra_tabs = lambda _driver: None
utils_stub.safe_get = lambda *_args, **_kwargs: None
sys.modules["utils"] = utils_stub

import pub_y2b


class FakeElement:
    def __init__(self, name):
        self.name = name

    def clear(self):
        raise AssertionError("contenteditable fields must not use clear()")

    def send_keys(self, *_args):
        raise AssertionError("contenteditable fields must not use send_keys()")


class FakeDriver:
    def __init__(self):
        self.elements = [FakeElement("title"), FakeElement("description")]
        self.scripts = []
        self.cdp_commands = []

    def execute_script(self, script, *args):
        self.scripts.append((script, args))

    def execute_cdp_cmd(self, command, params):
        self.cdp_commands.append((command, params))


class FakeWait:
    def __init__(self, driver, _timeout):
        self.driver = driver

    def until(self, _condition):
        return self.driver.elements.pop(0)


class YouTubeMetadataTests(unittest.TestCase):
    def test_reviewed_title_is_exact_and_has_no_hashtag_suffix(self):
        metadata = {
            "title": "光の雨 — Reviewed title 🎵",
            "tags": ["music", "人工智能"],
        }

        title = pub_y2b.reviewed_video_title(metadata)
        publisher = pub_y2b.YouTubePublisher(None, "video.mp4", "cover.jpg", metadata)

        self.assertEqual(title, metadata["title"])
        self.assertEqual(
            publisher.create_video_title_with_limited_tags(metadata), metadata["title"]
        )
        self.assertNotIn("#music", title)
        self.assertNotIn("#人工智能", title)

    def test_video_details_use_exact_cdp_text_for_unicode_multiline_urls(self):
        description = (
            "第一行：保留 Unicode 与换行 🎵\n"
            "Project: https://example.com/path?q=one&lang=zh-CN\n"
            "Listen: https://music.example.org/watch?v=a_b-c#section\n"
            "最後の行"
        )
        metadata = {
            "title": "Exact reviewed title",
            "long_description": description,
            "tags": ["must-stay-in-tags-field"],
        }
        driver = FakeDriver()
        publisher = pub_y2b.YouTubePublisher(
            driver,
            video_path="video.mp4",
            thumbnail_path="cover.jpg",
            metadata=metadata,
        )

        with (
            patch.object(pub_y2b, "WebDriverWait", FakeWait),
            patch.object(pub_y2b.time, "sleep", return_value=None),
        ):
            publisher.set_video_details()

        self.assertEqual(
            driver.cdp_commands,
            [
                ("Input.insertText", {"text": metadata["title"]}),
                ("Input.insertText", {"text": description}),
            ],
        )
        self.assertEqual(description.count("https://"), 2)
        self.assertIn("\n", driver.cdp_commands[1][1]["text"])
        self.assertNotIn(
            "#must-stay-in-tags-field", driver.cdp_commands[0][1]["text"]
        )
        self.assertEqual(len(driver.scripts), 2)
        self.assertTrue(
            all("selectNodeContents" in script for script, _args in driver.scripts)
        )


if __name__ == "__main__":
    unittest.main()
