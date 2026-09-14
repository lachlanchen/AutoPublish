import unittest

from douyin_submit import upload_outcome


class UploadStatusTests(unittest.TestCase):
    def test_reupload_inside_failure_is_not_completion(self):
        self.assertEqual(upload_outcome("video.mp4\n上传失败，重新上传"), "failed")

    def test_failure_wins_over_an_old_ready_control(self):
        self.assertEqual(upload_outcome("重新上传\n上传异常"), "failed")

    def test_in_progress_wins_over_a_replace_control(self):
        self.assertEqual(upload_outcome("替换视频\n正在上传 70%"), "pending")

    def test_exact_visible_completion_control_is_ready(self):
        self.assertEqual(upload_outcome("预览视频\n 重新上传 \n检测中10%"), "ready")

    def test_upload_instructions_do_not_imply_completion(self):
        self.assertEqual(upload_outcome("点击上传\n上传视频\n视频大小和格式"), "pending")
        self.assertEqual(upload_outcome("可以重新上传文件"), "pending")

    def test_empty_or_unavailable_page_remains_pending(self):
        self.assertEqual(upload_outcome(""), "pending")
        self.assertEqual(upload_outcome(None), "pending")


if __name__ == "__main__":
    unittest.main()
