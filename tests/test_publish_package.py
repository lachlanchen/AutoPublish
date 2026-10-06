import io
from pathlib import Path
import tempfile
import unittest
import zipfile

from publish_package import store_publish_package


def package(text="one"):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("song_metadata.json", text)
    return buffer.getvalue()


class PublishPackageTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "song.zip"
        self.original = package()
        self.path.write_bytes(self.original)

    def test_missing_body_cannot_destroy_existing_package(self):
        for body in (b"", b"filename=song.zip&publish_douyin=true", b"--multipart\r\nfilename\r\n"):
            with self.assertRaisesRegex(ValueError, "raw ZIP bytes"):
                store_publish_package(self.path, body)
            self.assertEqual(self.path.read_bytes(), self.original)

    def test_valid_explicit_reuse(self):
        digest = store_publish_package(self.path, b"", reuse_existing=True)
        self.assertEqual(len(digest), 64)
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_reuse_rejects_corrupt_archive(self):
        self.path.write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError, "Invalid publication ZIP"):
            store_publish_package(self.path, b"", reuse_existing=True)

    def test_reuse_rejects_missing_archive(self):
        self.path.unlink()
        with self.assertRaisesRegex(ValueError, "does not exist"):
            store_publish_package(self.path, b"", reuse_existing=True)

    def test_equal_size_is_not_equal_content(self):
        replacement = package("two")
        self.assertEqual(len(replacement), len(self.original))
        store_publish_package(self.path, replacement)
        self.assertEqual(self.path.read_bytes(), replacement)

    def test_active_job_blocks_replacement_but_allows_identical_bytes(self):
        store_publish_package(self.path, self.original, allow_replace=False)
        with self.assertRaises(FileExistsError):
            store_publish_package(self.path, package("two"), allow_replace=False)
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_unsafe_member_rejected_without_overwrite(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("../escape", "data")
        with self.assertRaisesRegex(ValueError, "unsafe"):
            store_publish_package(self.path, buffer.getvalue())
        self.assertEqual(self.path.read_bytes(), self.original)


if __name__ == "__main__":
    unittest.main()
