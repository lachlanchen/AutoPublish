import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from browser_asset_cache import load_assets


class BrowserAssetCacheTests(unittest.TestCase):
    def test_only_original_digest_verified_public_wasm_allowed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            payload = b'\x00asm\x01\x00\x00\x00'
            (root / 'vts.wasm').write_bytes(payload)
            entry = {'url': 'https://aladin.wxqcloud.qq.com/aladin/ffmepeg/finder-helper-media/v1/vts.wasm',
                     'file': 'vts.wasm', 'sha256': hashlib.sha256(payload).hexdigest()}
            manifest = root / 'browser-assets.json'
            manifest.write_text(json.dumps({'assets': [entry]}))
            self.assertEqual(len(load_assets(manifest)), 1)
            for change in [{'sha256': 'bad'}, {'url': 'https://channels.weixin.qq.com/private-api'},
                           {'url': entry['url'] + '?secret=x'}, {'file': '../vts.wasm'}]:
                manifest.write_text(json.dumps({'assets': [{**entry, **change}]}))
                with self.subTest(change=change), self.assertRaises(ValueError):
                    load_assets(manifest)

    def test_missing_manifest_is_noop(self):
        self.assertEqual(load_assets(Path('/not-installed/browser-assets.json')), {})


if __name__ == '__main__':
    unittest.main()
