import unittest
from instagram_caption import build_instagram_caption


class CaptionTests(unittest.TestCase):
    def test_japanese_english_chinese_order(self):
        metadata = {"title": "中文", "middle_description": "感谢摄影", "tags": ["旅行"],
                    "english_version": {"title": "English", "middle_description": "A journey"},
                    "japanese_version": {"title": "日本語", "middle_description": "旅の物語"}}
        result = build_instagram_caption(metadata)
        self.assertLess(result.index("日本語"), result.index("English"))
        self.assertLess(result.index("English"), result.index("中文"))
        self.assertIn("感谢摄影", result)

    def test_long_captions_preserve_all_languages(self):
        metadata = {"title": "ZH", "long_description": "中" * 3000,
                    "english_version": {"title": "EN", "long_description": "e" * 5000},
                    "japanese_version": {"title": "JA", "long_description": "あ" * 4000}}
        result = build_instagram_caption(metadata)
        self.assertLessEqual(len(result), 2200)
        self.assertTrue(all(tag in result for tag in ["JA", "EN", "ZH"]))

    def test_legacy_duplicates_empty_and_malformed_values(self):
        self.assertEqual(build_instagram_caption(None), "")
        self.assertEqual(build_instagram_caption({}), "")
        self.assertEqual(build_instagram_caption({"title": "Only", "english_version": {"title": "Only"}}), "Only")
        self.assertEqual(build_instagram_caption({"title": "中文", "japanese_version": None,
            "english_version": {"title": "English"}, "tags": "not-a-list"}), "English\n\n中文")

    def test_prefers_concise_description_and_reclaims_unused_budget(self):
        result = build_instagram_caption({"title": "ZH", "middle_description": "short",
            "long_description": "do not use", "tags": ["#one", "one", None],
            "japanese_version": {"title": "JA", "long_description": "あ" * 3000}})
        self.assertIn("short", result)
        self.assertNotIn("do not use", result)
        self.assertEqual(result.count("#one"), 1)
        self.assertGreater(len(result), 2100)


if __name__ == '__main__':
    unittest.main()
