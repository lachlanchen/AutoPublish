"""Opt-in, digest-pinned cache for public Shipinhao WebAssembly dependencies.

This supplies the vendor's original bytes when its CDN is unreachable. It never
intercepts authenticated APIs or replaces platform validation/success responses.
"""
import base64
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import threading

import requests
import websocket


PUBLIC_WASM = re.compile(
    r'https://aladin\.wxqcloud\.qq\.com/aladin/ffmepeg/'
    r'(?:rhino-media-suite/[\d.]+/rhino_video|finder-helper-media/v\d+/vts)\.wasm\Z'
)


def load_assets(manifest):
    if not manifest.is_file():
        return {}
    assets = {}
    for entry in json.loads(manifest.read_text())['assets']:
        url = entry['url']
        if not PUBLIC_WASM.fullmatch(url):
            raise ValueError('Only reviewed public Shipinhao WASM assets may be cached')
        path = manifest.parent / entry['file']
        if path.is_symlink() or path.resolve().parent != manifest.parent.resolve():
            raise ValueError('Cached asset must be a regular file beside its manifest')
        data = path.read_bytes()
        if not data.startswith(b'\x00asm\x01\x00\x00\x00') or hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise ValueError('Cached WebAssembly integrity check failed')
        assets[url] = base64.b64encode(data).decode('ascii')
    return assets


class AssetCache:
    def __init__(self, socket_url, assets):
        self.assets = assets
        self.socket = websocket.create_connection(socket_url, suppress_origin=True, timeout=2)
        self.stop = threading.Event()
        self.serial = 0
        self.send('Fetch.enable', {'patterns': [
            {'urlPattern': url, 'requestStage': 'Request'} for url in assets]})
        response = json.loads(self.socket.recv())
        if response.get('error'):
            self.socket.close()
            raise RuntimeError('Could not enable public asset cache')
        self.thread = threading.Thread(target=self.run, daemon=True, name='shipinhao-public-assets')
        self.thread.start()

    def send(self, method, params):
        self.serial += 1
        self.socket.send(json.dumps({'id': self.serial, 'method': method, 'params': params}))

    def run(self):
        try:
            while not self.stop.is_set():
                try:
                    message = json.loads(self.socket.recv())
                except websocket.WebSocketTimeoutException:
                    continue
                if message.get('method') != 'Fetch.requestPaused':
                    continue
                event = message['params']
                url = event['request']['url']
                body = self.assets.get(url)
                if body is None:
                    self.send('Fetch.continueRequest', {'requestId': event['requestId']})
                    continue
                self.send('Fetch.fulfillRequest', {
                    'requestId': event['requestId'], 'responseCode': 200,
                    'responseHeaders': [
                        {'name': 'Content-Type', 'value': 'application/wasm'},
                        {'name': 'Access-Control-Allow-Origin', 'value': '*'},
                        {'name': 'Cross-Origin-Resource-Policy', 'value': 'cross-origin'},
                        {'name': 'Cache-Control', 'value': 'public, max-age=31536000'},
                    ], 'body': body,
                })
                print(f'Served verified public dependency: {url}', flush=True)
        except Exception as exc:
            print(f'Public dependency cache stopped: {type(exc).__name__}', flush=True)
        finally:
            try:
                self.send('Fetch.disable', {})
            finally:
                self.socket.close()

    def close(self):
        self.stop.set()
        self.thread.join(timeout=5)


@contextmanager
def shipinhao_assets(driver, platform):
    cache = None
    try:
        if platform in {'ShiPinHao', 'ShiPinHaoMusic'}:
            manifest = Path(os.getenv('AUTOPUBLISH_BROWSER_ASSETS',
                                      str(Path.home() / '.cache/autopublish/browser-assets.json')))
            assets = load_assets(manifest)
            if assets:
                address = driver.capabilities['goog:chromeOptions']['debuggerAddress']
                if not re.fullmatch(r'(?:127\.0\.0\.1|localhost):\d+', address):
                    raise ValueError('Asset cache requires a loopback browser')
                pages = requests.get(f'http://{address}/json/list', timeout=10).json()
                target = driver.current_window_handle.removeprefix('CDwindow-')
                page = next(p for p in pages if p['id'] == target)
                cache = AssetCache(page['webSocketDebuggerUrl'], assets)
        yield
    finally:
        if cache:
            cache.close()
