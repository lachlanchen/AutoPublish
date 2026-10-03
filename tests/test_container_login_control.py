"""Private browser control must not interrupt a publish or accept another endpoint."""
import importlib.util
import io
import json
from pathlib import Path
import queue
import sys
import threading
import types
from unittest.mock import patch

import tornado.testing
from tornado.web import Application


class TestContainerLoginControl(tornado.testing.AsyncHTTPTestCase):
    def runTest(self):
        pass  # Compatibility with pytest versions that inspect a default instance.

    def get_app(self):
        self.publisher = types.SimpleNamespace(
            is_publishing=False, PUBLISH_QUEUE=queue.Queue(),
            BROWSER_CONTROL_LOCK=threading.Lock(),
        )
        path = Path(__file__).resolve().parents[1] / "container_runtime.py"
        spec = importlib.util.spec_from_file_location("private_login_test", path)
        self.module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"app": self.publisher}):
            spec.loader.exec_module(self.module)
        return Application([(r"/platform-login", self.module.PlatformLoginHandler)])

    def close(self, platform="shipinhao"):
        return self.fetch("/platform-login", method="DELETE", body=json.dumps({"platform": platform}), allow_nonstandard_methods=True)

    def test_active_publish_and_unknown_platform_never_touch_browser(self):
        with patch.object(self.module.urllib.request, "urlopen") as request:
            self.publisher.is_publishing = True
            assert self.close().code == 409
            self.publisher.is_publishing = False
            self.publisher.PUBLISH_QUEUE.put({"id": "fixture"})
            assert self.close().code == 409
            assert self.close("file:///etc/passwd").code == 400
            request.assert_not_called()

    def test_only_selected_loopback_browser_can_close(self):
        calls = []
        socket = types.SimpleNamespace(send=lambda value: calls.append(json.loads(value)), close=lambda: None)
        import websocket
        data = {"webSocketDebuggerUrl": "ws://127.0.0.1:5006/devtools/browser/test"}
        with patch.object(self.module.urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(data).encode())) as request, patch.object(websocket, "create_connection", return_value=socket) as connect:
            assert self.close().code == 200
            assert request.call_args.args[0] == "http://127.0.0.1:5006/json/version"
            assert connect.call_args.args[0] == data["webSocketDebuggerUrl"]
            assert calls == [{"id": 1, "method": "Browser.close"}]
        assert not self.publisher.BROWSER_CONTROL_LOCK.locked()
        data["webSocketDebuggerUrl"] = "ws://evil.test/devtools/browser/test"
        with patch.object(self.module.urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(data).encode())), patch.object(websocket, "create_connection") as connect:
            assert self.close().code == 500
            connect.assert_not_called()
        assert not self.publisher.BROWSER_CONTROL_LOCK.locked()
