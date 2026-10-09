"""Browser fixture for the platform's asynchronous, click-to-toggle dropdown."""
import ast
from pathlib import Path
import unittest

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


@unittest.skipUnless(sync_playwright, 'Playwright is needed for the DOM regression test')
class MusicDropdownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path(__file__).resolve().parents[1] / 'pub_shipinhao_music.py'
        cls.script = next(ast.literal_eval(n.value) for n in ast.parse(source.read_text()).body
                          if isinstance(n, ast.Assign) and any(
                              isinstance(t, ast.Name) and t.id == 'SELECT_BY_LABEL_SCRIPT' for t in n.targets))
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def test_language_menu_remains_open_until_option_rendered_and_verified(self):
        page = self.browser.new_page()
        self.addCleanup(page.close)
        page.set_content('''<div class="normal-input-wrap"><div class="label-font">语言</div>
          <div class="content"><input placeholder="请选择" value="普通话">
          <ul style="display:none"><li class="weui-desktop-dropdown__list-ele">普通话</li>
          <li class="weui-desktop-dropdown__list-ele">日语</li></ul></div></div>
          <script>
          const input=document.querySelector('input'), menu=document.querySelector('ul');
          input.onclick=()=>setTimeout(()=>menu.style.display=menu.style.display==='none'?'block':'none',0);
          document.querySelectorAll('li').forEach(li=>li.onclick=()=>setTimeout(()=>{
            input.value=li.textContent; menu.style.display='none';
          },0));
          </script>''')
        run = lambda: page.evaluate('(s)=>Function(s)("语言","日语")', self.script)
        self.assertFalse(run()['ok'])
        page.wait_for_timeout(30)
        self.assertFalse(run()['ok'], 'Do not claim success before Vue commits the value')
        page.wait_for_timeout(30)
        self.assertEqual(run(), {'ok': True, 'selected': '日语', 'alreadySelected': True})
        self.assertEqual(page.locator('input').input_value(), '日语')
        self.assertEqual(run()['selected'], '日语', 'Polling must not reopen/reset a correct value')


if __name__ == '__main__':
    unittest.main()
