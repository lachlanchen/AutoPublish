import base64
from pathlib import Path
import tempfile
import unittest

import requests

from browser_asset_cache import AssetCache

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


@unittest.skipUnless(sync_playwright, 'Playwright is needed for the worker regression test')
class WorkerAssetCacheTests(unittest.TestCase):
    def test_exact_vendor_dependency_can_be_served_to_a_dedicated_worker(self):
        url = 'https://aladin.wxqcloud.qq.com/aladin/ffmepeg/finder-helper-media/v1/vts.wasm'
        data = b'\x00asm\x01\x00\x00\x00'
        with tempfile.TemporaryDirectory() as profile, sync_playwright() as runtime:
            browser = runtime.chromium.launch_persistent_context(
                profile, headless=True, args=['--remote-debugging-port=0'])
            cache = None
            try:
                port = (Path(profile) / 'DevToolsActivePort').read_text().splitlines()[0]
                version = requests.get(f'http://127.0.0.1:{port}/json/version', timeout=10).json()
                cache = AssetCache(version['webSocketDebuggerUrl'], {url: base64.b64encode(data).decode()})
                page = browser.pages[0]
                result = page.evaluate('''url => new Promise((resolve, reject) => {
                  const timeout = setTimeout(() => reject(new Error('Worker download timed out')), 15000);
                  const code = `fetch(${JSON.stringify(url)}).then(r=>r.arrayBuffer()).then(b=>postMessage([...new Uint8Array(b)])).catch(e=>postMessage({error:String(e)}));`;
                  const worker = new Worker(URL.createObjectURL(new Blob([code], {type:'text/javascript'})));
                  worker.onmessage = event => {clearTimeout(timeout);worker.terminate();resolve(event.data);};
                })''', url)
                self.assertEqual(result, list(data))
            finally:
                if cache:
                    cache.close()
                browser.close()


if __name__ == '__main__':
    unittest.main()
