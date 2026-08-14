import unittest
from unittest.mock import MagicMock, patch

from scripts.manage_y2b_videos import move_to_playlist


class YouTubePlaylistSafetyTests(unittest.TestCase):
    @patch("scripts.manage_y2b_videos.click_save")
    @patch("scripts.manage_y2b_videos.YouTubePublisher")
    @patch("scripts.manage_y2b_videos.open_edit_page")
    def test_failed_playlist_selection_does_not_save(
        self,
        open_edit_page,
        publisher_class,
        click_save,
    ):
        publisher_class.return_value.set_playlist.return_value = False

        result = move_to_playlist(MagicMock(), "video-id", "LALACHAN", apply=True)

        open_edit_page.assert_called_once()
        click_save.assert_not_called()
        self.assertFalse(result["selected"])
        self.assertFalse(result["saved"])

    @patch("scripts.manage_y2b_videos.click_save", return_value=True)
    @patch("scripts.manage_y2b_videos.YouTubePublisher")
    @patch("scripts.manage_y2b_videos.open_edit_page")
    def test_successful_playlist_selection_saves(
        self,
        open_edit_page,
        publisher_class,
        click_save,
    ):
        publisher_class.return_value.set_playlist.return_value = True

        result = move_to_playlist(MagicMock(), "video-id", "LALACHAN", apply=True)

        click_save.assert_called_once()
        self.assertTrue(result["selected"])
        self.assertTrue(result["saved"])


if __name__ == "__main__":
    unittest.main()
