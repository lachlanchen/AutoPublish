"""Opt-in, digest-pinned cache for public Shipinhao WebAssembly dependencies.

This supplies the vendor's original bytes when its CDN is unreachable. It never
intercepts authenticated APIs or replaces platform validation/success responses.
"""
import base64
from collections import deque
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import threading
from urllib.parse import parse_qsl, urlsplit, urlunsplit

import requests
import websocket


PUBLIC_WASM = re.compile(
    r'https://aladin\.wxqcloud\.qq\.com/aladin/ffmepeg/'
    r'(?:rhino-media-suite/[\d.]+/rhino_video|finder-helper-media/v\d+/vts)\.wasm\Z'
)


def asset_url(request_url):
    parts = urlsplit(request_url)
    if parts.fragment or any(key not in {'_rid', '_pageUrl'} for key, _ in parse_qsl(parts.query)):
        return None
    # The site's telemetry appends these two parameters to the same static
    # binary. Never normalize unknown/signature/auth parameters or log values.
    return urlunsplit((parts.scheme, parts.netloc, parts.path, '', ''))


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
        self.pending = deque()
        self.patterns = {'patterns': [
            {'urlPattern': pattern, 'requestStage': 'Request'}
            for url in assets for pattern in (url, url + '?*')]}
        self.send('Fetch.enable', self.patterns)
        while True:
            response = json.loads(self.socket.recv())
            if response.get('id') == self.serial:
                break
            self.pending.append(response)
        if response.get('error'):
            self.socket.close()
            raise RuntimeError('Could not enable public asset cache')
        self.thread = threading.Thread(target=self.run, daemon=True, name='shipinhao-public-assets')
        self.thread.start()

    def send(self, method, params):
        self.serial += 1
        message = {'id': self.serial, 'method': method, 'params': params}
        self.socket.send(json.dumps(message))

    def run(self):
        try:
            while not self.stop.is_set():
                try:
                    message = self.pending.popleft() if self.pending else json.loads(self.socket.recv())
                except websocket.WebSocketTimeoutException:
                    continue
                if message.get('method') != 'Fetch.requestPaused':
                    continue
                event = message['params']
                url = asset_url(event['request']['url'])
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
                # Browser-level Fetch covers dedicated-worker downloads too;
                # the worker's own CDP session does not implement Fetch.
                version = requests.get(f'http://{address}/json/version', timeout=10).json()
                cache = AssetCache(version['webSocketDebuggerUrl'], assets)
        yield
    finally:
        if cache:
            cache.close()
