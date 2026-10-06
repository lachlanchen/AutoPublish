import unittest
from unittest.mock import Mock

from publish_batch import publish_batch


class PublishBatchTests(unittest.TestCase):
    def test_failed_upload_does_not_block_other_platforms(self):
        record = Mock()
        publish = Mock(side_effect=[RuntimeError("upload failed"), True, True])
        with self.assertRaisesRegex(RuntimeError, "retry only failed targets: Douyin"):
            publish_batch([(1, "Douyin"), (2, "ShiPinHao"), (3, "YouTube")], publish, on_result=record)
        self.assertEqual(publish.call_count, 3)
        self.assertEqual(record.call_args_list[-1].args, ("YouTube", {"status": "done", "error": None}))
        self.assertEqual(record.call_args_list[1].args, ("Douyin", {"status": "failed", "error": "upload failed"}))

    def test_all_success_and_focus_are_recorded(self):
        focus = Mock()
        result = publish_batch([(1, "Instagram")], lambda *_: True, before_each=focus)
        self.assertEqual(result, {"Instagram": {"status": "done", "error": None}})
        focus.assert_called_once_with("Instagram")

    def test_false_return_is_failure(self):
        with self.assertRaisesRegex(RuntimeError, "unsuccessful"):
            publish_batch([(1, "Douyin")], lambda *_: False)

    def test_focus_failure_does_not_block_next_target(self):
        publish = Mock(return_value=True)
        with self.assertRaisesRegex(RuntimeError, "focus failed"):
            publish_batch([(1, "Douyin"), (2, "YouTube")], publish,
                          before_each=Mock(side_effect=[RuntimeError("focus failed"), None]))
        publish.assert_called_once_with(2, "YouTube")


if __name__ == "__main__":
    unittest.main()
