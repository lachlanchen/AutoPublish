import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from published_retention import cleanup_published, sha256


class PublishedRetentionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / 'song'
        self.directory.mkdir()
        self.archive = self.directory / 'song.zip'
        with zipfile.ZipFile(self.archive, 'w') as archive:
            archive.writestr('song.mp4', b'video')
            archive.writestr('song_lyrics.txt', b'corrected lyric')
            archive.writestr('song_metadata.json', '{}')
        with zipfile.ZipFile(self.archive) as archive:
            archive.extractall(self.directory)
        self.job = dict(id='job-1', filename='song.zip', status='done',
                        package_sha256=sha256(self.archive), zip_path=str(self.archive),
                        transcription_dir=str(self.directory), local_package=False,
                        test_mode=False, platforms=['shipinhao', 'youtube'],
                        platform_results={'ShiPinHao': {'status': 'done'}, 'YouTube': {'status': 'done'}})

    def test_dry_run_preserves_everything(self):
        self.assertEqual(len(cleanup_published([self.job], self.root)), 1)
        self.assertTrue(self.archive.exists())

    def test_confirmed_cleanup_keeps_corrected_lyrics_metadata_and_receipt(self):
        unrelated = self.directory / 'manual-original.wav'
        unrelated.write_bytes(b'never remove')
        reports = cleanup_published([self.job], self.root, apply=True)
        self.assertFalse(self.archive.exists())
        self.assertFalse((self.directory / 'song.mp4').exists())
        for name in ['song_lyrics.txt', 'song_metadata.json', unrelated.name]:
            self.assertTrue((self.directory / name).exists())
        receipt = next((self.root / '.published-receipts').glob('*.json'))
        self.assertEqual(json.loads(receipt.read_text())['jobs'][0]['status'], 'removed')
        self.assertEqual(reports[0]['platforms'], ['shipinhao', 'youtube'])
        self.assertEqual(cleanup_published([self.job], self.root, apply=True), [])

    def test_partial_failure_and_empty_results_never_clean(self):
        for results in [{}, {'YouTube': {'status': 'done'}, 'ShiPinHao': {'status': 'failed'}}]:
            self.assertEqual(cleanup_published([{**self.job, 'platform_results': results}], self.root), [])

    def test_failed_batch_then_scoped_retry_completes_all_targets(self):
        failed = {**self.job, 'status': 'failed', 'platform_results': {
            'YouTube': {'status': 'done'}, 'ShiPinHao': {'status': 'failed'}}}
        retry = {**self.job, 'id': 'job-2', 'platforms': ['shipinhao'],
                 'platform_results': {'ShiPinHao': {'status': 'done'}}}
        self.assertEqual(len(cleanup_published([failed, retry], self.root)), 1)

    def test_active_test_local_changed_or_unknown_are_preserved(self):
        for change in [{'status': 'running'}, {'status': 'queued'}, {'test_mode': True},
                       {'local_package': True}, {'package_sha256': 'different'},
                       {'package_sha256': None}, {'platforms': []}, {'platforms': ['unknown']},
                       {'zip_path': '/some/source/song.zip'}, {'transcription_dir': '/'}]:
            with self.subTest(change=change):
                self.assertEqual(cleanup_published([{**self.job, **change}], self.root), [])

    def test_any_active_job_for_same_name_blocks_cleanup(self):
        other = {**self.job, 'id': 'job-2', 'package_sha256': 'new', 'status': 'queued'}
        self.assertEqual(cleanup_published([self.job, other], self.root), [])

    def test_symlinked_media_or_directory_never_deleted(self):
        external = self.root / 'original.mp4'
        external.write_bytes(b'original')
        media = self.directory / 'song.mp4'
        media.unlink()
        media.symlink_to(external)
        cleanup_published([self.job], self.root, apply=True)
        self.assertTrue(external.exists())
        self.assertTrue(media.is_symlink())

    def test_changed_archive_does_not_borrow_old_success(self):
        with zipfile.ZipFile(self.archive, 'a') as archive:
            archive.writestr('new.mp4', b'new')
        self.assertEqual(cleanup_published([self.job], self.root), [])

    def test_changed_extracted_media_is_not_deleted(self):
        media = self.directory / 'song.mp4'
        media.write_bytes(b'new source not in uploaded archive')
        cleanup_published([self.job], self.root, apply=True)
        self.assertTrue(media.exists())

    def test_symlinked_package_directory_is_never_traversed(self):
        real = self.root / 'source'
        self.directory.rename(real)
        self.directory.symlink_to(real, target_is_directory=True)
        self.assertEqual(cleanup_published([self.job], self.root, apply=True), [])
        self.assertTrue((real / 'song.zip').exists())


if __name__ == '__main__':
    unittest.main()
