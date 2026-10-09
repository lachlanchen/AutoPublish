"""Readiness must follow real upload state and asynchronous form validation."""
import ast
from pathlib import Path
import unittest

from playwright.sync_api import sync_playwright


class MusicReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path(__file__).resolve().parents[1] / 'pub_shipinhao_music.py'
        cls.scripts = {n.targets[0].id: ast.literal_eval(n.value)
                       for n in ast.parse(source.read_text()).body
                       if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
                       and n.targets[0].id in {'MUSIC_VALIDATION_STATE_SCRIPT',
                                              'MUSIC_SUBMITTED_STATE_SCRIPT'}}
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def setUp(self):
        self.page = self.browser.new_page()
        self.addCleanup(self.page.close)
        self.page.set_content('<div id="root"></div><div id="upload"></div>')
        self.page.evaluate('''() => {
          window.valid = true;
          const store = {formRef: {musicInfo: 'musicInfo'},
            songInfo: {originalDataUrl: 'private-upload-url'},
            albumInfo: {coverUrl: 'private-cover-url'}};
          document.querySelector('#root').__vue__ = {postMusicStore: store,
            $data: {hasCheckLawText: true}, hasCheckLawText: true,
            $refs: {musicInfo: {validate: async () => {
              await new Promise(resolve => setTimeout(resolve, 15)); return window.valid;
            }}}};
          document.querySelector('#upload').__vue__ = {
            $data: {uploading: false}, uploading: false, errorMessage: ''};
        }''')

    def state(self):
        return self.page.evaluate('(s) => Function(s)()', self.scripts['MUSIC_VALIDATION_STATE_SCRIPT'])

    def test_waits_for_upload_even_when_button_would_be_enabled(self):
        self.page.evaluate("document.querySelector('#upload').__vue__.uploading = true")
        self.assertFalse(self.state()['ready'])
        self.page.evaluate("document.querySelector('#upload').__vue__.uploading = false")
        self.assertTrue(self.state()['ready'])

    def test_async_validation_can_fail_then_recover_without_reupload(self):
        self.page.evaluate('window.valid = false')
        self.assertFalse(self.state()['ready'])
        self.page.evaluate('window.valid = true')
        self.assertTrue(self.state()['ready'])
        self.assertNotIn('private-', str(self.state()))

    def test_missing_cover_or_agreement_blocks(self):
        self.page.evaluate("document.querySelector('#root').__vue__.postMusicStore.albumInfo.coverUrl = ''")
        self.assertFalse(self.state()['ready'])
        self.page.evaluate("document.querySelector('#root').__vue__.postMusicStore.albumInfo.coverUrl = 'cover'")
        self.page.evaluate("document.querySelector('#root').__vue__.hasCheckLawText = false")
        self.assertFalse(self.state()['ready'])

    def test_unknown_form_fails_closed(self):
        self.page.set_content('<button>Publish</button>')
        self.assertFalse(self.state()['ready'])

    def test_explicit_submit_confirmation_required(self):
        run = lambda: self.page.evaluate('(s) => Function(s)()', self.scripts['MUSIC_SUBMITTED_STATE_SCRIPT'])
        self.assertFalse(run()['submitted'])
        self.page.set_content('<p>你的音乐已提交，预计需要1-3个工作日审核。</p>')
        self.assertTrue(run()['submitted'])


if __name__ == '__main__':
    unittest.main()
