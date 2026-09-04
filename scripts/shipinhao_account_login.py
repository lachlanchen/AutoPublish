#!/usr/bin/env python3
"""Log a named, isolated Chromium profile into Shipinhao.

This helper is deliberately separate from the normal AutoPublish queue.  It
owns only a named Chromium profile and a loopback HTTP server containing the
current login QR.  A camera-side tool may consume ``/qr.png`` without sharing
browser files or controlling this process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from load_env import load_env  # noqa: E402


CREATE_URL = "https://channels.weixin.qq.com/platform/post/create"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_QR_BYTES = 5 * 1024 * 1024
RESERVED_AUTOPUBLISH_DEBUG_PORTS = {5003, 5004, 5005, 5006, 5007, 9222}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_profile_name(value: str) -> str:
    name = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value or "")).strip("-.")
    if not name:
        raise ValueError("Account profile name cannot be empty.")
    return name[:64]


def isolated_profile_dir(profile: str, requested: Path | None = None) -> Path:
    """Resolve only the helper-owned profile path, never a legacy profile."""
    expected = (
        Path.home() / f"chromium_dev_session_shipinhao_{profile}"
    ).expanduser().resolve()
    if requested is None:
        return expected
    resolved = requested.expanduser().resolve()
    if resolved != expected:
        raise ValueError(
            "The standalone helper only accepts its isolated named profile path: "
            f"{expected}"
        )
    return resolved


def validate_ports(debug_port: int, server_port: int) -> None:
    if not (1024 <= debug_port <= 65535 and 1024 <= server_port <= 65535):
        raise ValueError("Ports must be between 1024 and 65535.")
    if debug_port in RESERVED_AUTOPUBLISH_DEBUG_PORTS:
        raise ValueError(
            f"Port {debug_port} is reserved for an existing AutoPublish browser profile."
        )
    if debug_port == server_port:
        raise ValueError("The Chromium debug port and QR server port must differ.")


def is_port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False


def browser_binary() -> str:
    configured = (
        os.environ.get("AUTOPUBLISH_BROWSER_BIN")
        or os.environ.get("CHROMIUM_BIN")
        or os.environ.get("CHROME_BIN")
    )
    if configured:
        return configured
    is_arm = platform.machine().lower().startswith(("arm", "aarch64"))
    candidates = (
        ("chromium-browser", "chromium", "google-chrome", "google-chrome-stable")
        if is_arm
        else ("google-chrome", "google-chrome-stable", "chromium-browser", "chromium")
    )
    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            return found
    raise RuntimeError("Chromium/Chrome was not found.")


def chromedriver_binary() -> str:
    configured = os.environ.get("AUTOPUBLISH_CHROMEDRIVER") or os.environ.get(
        "CHROMEDRIVER_PATH"
    )
    if configured and Path(configured).is_file():
        return configured
    for candidate in (
        "/usr/lib/chromium-browser/chromedriver",
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver",
        "/snap/bin/chromium.chromedriver",
    ):
        if Path(candidate).is_file():
            return candidate
    found = shutil.which("chromedriver")
    if found:
        return found
    raise RuntimeError("chromedriver was not found.")


def display_name() -> str:
    configured = os.environ.get("AUTOPUBLISH_DISPLAY") or os.environ.get("DISPLAY")
    if configured:
        return configured
    return ":1" if Path("/tmp/.X11-unix/X1").exists() else ":0"


def browser_flags() -> list[str]:
    configured = os.environ.get(
        "AUTOPUBLISH_CHROMIUM_FLAGS",
        "--disable-gpu --use-gl=swiftshader --enable-unsafe-swiftshader "
        "--disable-dev-shm-usage --password-store=basic",
    )
    return configured.split()


def matching_browser_process(
    port: int,
    profile_dir: Path,
    proc_root: Path = Path("/proc"),
) -> bool:
    expected_port = f"--remote-debugging-port={port}"
    expected_profile = f"--user-data-dir={profile_dir}"
    for command_path in proc_root.glob("[0-9]*/cmdline"):
        try:
            arguments = command_path.read_bytes().split(b"\0")
            decoded = [part.decode("utf-8", errors="replace") for part in arguments]
        except (OSError, PermissionError):
            continue
        if expected_port in decoded and expected_profile in decoded:
            return True
    return False


def start_named_browser(profile: str, profile_dir: Path, debug_port: int) -> None:
    if is_port_open(debug_port):
        if not matching_browser_process(debug_port, profile_dir):
            raise RuntimeError(
                f"Port {debug_port} belongs to another Chromium profile; refusing to touch it."
            )
        print(f"Reusing isolated Shipinhao profile {profile!r} on port {debug_port}.")
        return

    profile_dir.mkdir(parents=True, exist_ok=True)
    log_dir = Path.home() / "chromium_dev_session_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"chromium_shipinhao_{profile}.log"
    command = [
        browser_binary(),
        "--hide-crash-restore-bubble",
        *browser_flags(),
        f"--remote-debugging-port={debug_port}",
        f"--user-data-dir={profile_dir}",
        CREATE_URL,
    ]
    environment = {**os.environ, "DISPLAY": display_name()}
    with log_path.open("ab") as log_file:
        subprocess.Popen(
            command,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=log_file,
            start_new_session=True,
        )

    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if is_port_open(debug_port):
            print(
                f"Started isolated Shipinhao profile {profile!r}: "
                f"port={debug_port} dir={profile_dir}"
            )
            return
        time.sleep(0.5)
    raise RuntimeError(f"Chromium did not expose debug port {debug_port}.")


def create_driver(debug_port: int):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service

    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
    options.binary_location = browser_binary()
    return webdriver.Chrome(
        service=Service(chromedriver_binary()),
        options=options,
    )


class QrState:
    def __init__(self, root: Path, profile: str):
        self.root = root
        self.profile = profile
        self.qr_path = root / "qr.png"
        self._lock = threading.Lock()
        self._payload = {
            "status": "starting",
            "profile": profile,
            "updated_at": utc_now(),
            "revision": 0,
        }
        root.mkdir(parents=True, exist_ok=True)

    def require(self, artifact_path: str, message: str) -> None:
        data = Path(artifact_path).read_bytes()
        if not data.startswith(PNG_SIGNATURE):
            raise ValueError("Shipinhao login artifact is not a PNG.")
        if len(data) > MAX_QR_BYTES:
            raise ValueError("Shipinhao login QR exceeds the size limit.")
        digest = hashlib.sha256(data).hexdigest()
        with self._lock:
            if self._payload.get("sha256") != digest:
                temporary = self.qr_path.with_suffix(".tmp")
                temporary.write_bytes(data)
                os.replace(temporary, self.qr_path)
                revision = int(self._payload.get("revision") or 0) + 1
            else:
                revision = int(self._payload.get("revision") or 0)
            self._payload = {
                "status": "required",
                "profile": self.profile,
                "message": message,
                "revision": revision,
                "sha256": digest,
                "updated_at": utc_now(),
                "qr_url": "/qr.png",
            }

    def resolve(self, account_name: str | None = None) -> None:
        with self._lock:
            self._payload = {
                **self._payload,
                "status": "resolved",
                "account_name": account_name or self._payload.get("account_name"),
                "updated_at": utc_now(),
            }

    def fail(self, message: str) -> None:
        with self._lock:
            self._payload = {
                **self._payload,
                "status": "error",
                "message": message,
                "updated_at": utc_now(),
            }

    def snapshot(self) -> dict:
        with self._lock:
            return dict(self._payload)

    def qr_bytes(self) -> bytes | None:
        with self._lock:
            if self._payload.get("status") != "required" or not self.qr_path.is_file():
                return None
            return self.qr_path.read_bytes()


def handler_for(state: QrState):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            if self.client_address[0] not in {"127.0.0.1", "::1"}:
                self.send_error(403)
                return
            if self.path == "/status.json":
                body = json.dumps(state.snapshot(), ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
            elif self.path == "/qr.png":
                body = state.qr_bytes()
                if body is None:
                    self.send_error(404, "No current Shipinhao login QR")
                    return
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
            else:
                self.send_error(404)
                return
            self.send_header("Cache-Control", "no-store, max-age=0")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:
            return

    return Handler


def main() -> int:
    # Keep Selenium/login side effects out of module import so validation and
    # QR-state helpers remain independently testable.
    from login_shipinhao import ShiPinHaoLogin

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, help="Isolated account/profile label")
    parser.add_argument("--debug-port", type=int, default=5016)
    parser.add_argument("--server-port", type=int, default=8765)
    parser.add_argument("--profile-dir", type=Path)
    parser.add_argument("--login-wait-seconds", type=int, default=1800)
    parser.add_argument("--email", action="store_true", help="Also send the normal QR email")
    args = parser.parse_args()

    load_env()
    profile = safe_profile_name(args.profile)
    profile_dir = isolated_profile_dir(profile, args.profile_dir)
    validate_ports(args.debug_port, args.server_port)

    state_root = (
        Path.home() / ".local/state/autopublish/shipinhao-login" / profile
    )
    state = QrState(state_root, profile)
    server = ThreadingHTTPServer(
        ("127.0.0.1", args.server_port),
        handler_for(state),
    )
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"Shipinhao login QR server: http://127.0.0.1:{args.server_port}/qr.png")
    print(f"Shipinhao login status: http://127.0.0.1:{args.server_port}/status.json")

    os.environ["AUTOPUBLISH_LOGIN_WAIT_SECONDS"] = str(args.login_wait_seconds)
    try:
        start_named_browser(profile, profile_dir, args.debug_port)
        driver = create_driver(args.debug_port)

        def attention_callback(*, status, platform, kind, artifact_path=None, message=""):
            if platform != "shipinhao" or kind != "login_qr":
                return
            if status == "required" and artifact_path:
                state.require(artifact_path, message)
                print(
                    f"QR revision {state.snapshot()['revision']} is ready at "
                    f"http://127.0.0.1:{args.server_port}/qr.png"
                )
            elif status == "resolved":
                state.resolve()

        login = ShiPinHaoLogin(
            driver,
            port=str(args.debug_port),
            attention_callback=attention_callback,
            send_email=args.email,
            account_profile=profile,
        )
        login.check_and_act()
        state.resolve(login.last_account_name)
        print(json.dumps(state.snapshot(), ensure_ascii=False))
        return 0
    except Exception as error:
        state.fail(str(error))
        print(json.dumps(state.snapshot(), ensure_ascii=False), file=sys.stderr)
        return 1
    finally:
        # Give a polling camera client time to observe the terminal state.
        time.sleep(2)
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
