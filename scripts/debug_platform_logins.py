#!/usr/bin/env python3
"""Trigger AutoPublish platform login checks without uploading or publishing."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from load_env import load_env  # noqa: E402


PLATFORM_PORTS = {
    "xhs": 5003,
    "xiaohongshu": 5003,
    "douyin": 5004,
    "bilibili": 5005,
}


def _resolve_display() -> str:
    display = os.environ.get("AUTOPUBLISH_DISPLAY") or os.environ.get("DISPLAY")
    if display:
        return display
    if os.path.exists("/tmp/.X11-unix/X1"):
        return ":1"
    return ":0"


def _resolve_browser_bin() -> str:
    for key in ("AUTOPUBLISH_BROWSER_BIN", "CHROMIUM_BIN", "CHROME_BIN"):
        value = os.environ.get(key)
        if value:
            return value
    is_arm = platform.machine().lower().startswith(("arm", "aarch64"))
    candidates = (
        ["chromium-browser", "chromium", "google-chrome", "google-chrome-stable"]
        if is_arm
        else ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium"]
    )
    for name in candidates:
        found = shutil.which(name)
        if found:
            return found
    return "chromium-browser" if is_arm else "google-chrome"


def _resolve_session_prefix(browser_bin: str) -> str:
    return "chromium" if "chromium" in os.path.basename(browser_bin or "") else "chrome"


def _resolve_chromedriver_path() -> str:
    for key in ("AUTOPUBLISH_CHROMEDRIVER", "CHROMEDRIVER_PATH"):
        value = os.environ.get(key)
        if value and os.path.exists(value):
            return value
    for candidate in (
        "/usr/lib/chromium-browser/chromedriver",
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver",
        "/snap/bin/chromium.chromedriver",
    ):
        if os.path.exists(candidate):
            return candidate
    return shutil.which("chromedriver") or "/usr/lib/chromium-browser/chromedriver"


def _browser_flags() -> list[str]:
    value = os.environ.get(
        "AUTOPUBLISH_CHROMIUM_FLAGS",
        "--disable-gpu --use-gl=swiftshader --use-angle=swiftshader --enable-unsafe-swiftshader --disable-dev-shm-usage --remote-allow-origins=*",
    )
    return [part for part in value.split() if part]


def _is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _start_browser_if_needed(platform_name: str, port: int, url: str) -> None:
    if _is_port_open("127.0.0.1", port):
        print(f"Reusing existing {platform_name} Chromium session on port {port}.")
        return
    browser_bin = _resolve_browser_bin()
    prefix = _resolve_session_prefix(browser_bin)
    display = _resolve_display()
    profile_dir = Path.home() / f"{prefix}_dev_session_{port}"
    log_dir = Path.home() / f"{prefix}_dev_session_logs"
    profile_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{prefix}_{platform_name}.log"
    cmd = [
        browser_bin,
        "--hide-crash-restore-bubble",
        *_browser_flags(),
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        url,
    ]
    env = {**os.environ, "DISPLAY": display}
    with open(log_file, "ab") as log:
        subprocess.Popen(cmd, env=env, stdout=log, stderr=log)
    time.sleep(5)


def create_new_driver(port: int):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service

    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
    browser_bin = _resolve_browser_bin()
    if browser_bin and os.path.exists(browser_bin):
        options.binary_location = browser_bin
    return webdriver.Chrome(service=Service(_resolve_chromedriver_path()), options=options)


def _normalize_platforms(values: list[str]) -> list[str]:
    normalized = []
    for value in values:
        for part in value.split(","):
            key = part.strip().lower()
            if not key:
                continue
            if key == "all":
                for item in ("xhs", "douyin", "bilibili"):
                    if item not in normalized:
                        normalized.append(item)
                continue
            if key not in PLATFORM_PORTS:
                raise SystemExit(f"Unknown platform: {part}")
            canonical = "xhs" if key == "xiaohongshu" else key
            if canonical not in normalized:
                normalized.append(canonical)
    return normalized or ["xhs", "douyin", "bilibili"]


def main() -> int:
    try:
        sys.stdout.reconfigure(line_buffering=True)
        sys.stderr.reconfigure(line_buffering=True)
    except Exception:
        pass

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--platforms",
        nargs="*",
        default=["all"],
        help="Platforms to check: xhs, douyin, bilibili, all. Comma-separated values are accepted.",
    )
    parser.add_argument(
        "--login-wait-seconds",
        type=int,
        default=None,
        help="Override AUTOPUBLISH_LOGIN_WAIT_SECONDS for this run.",
    )
    args = parser.parse_args()

    if args.login_wait_seconds:
        os.environ["AUTOPUBLISH_LOGIN_WAIT_SECONDS"] = str(args.login_wait_seconds)

    os.environ["DISPLAY"] = _resolve_display()
    load_env()
    from login_bilibili import BilibiliLogin
    from login_douyin import DouyinLogin
    from login_xiaohongshu import XiaoHongShuLogin
    from utils import bring_to_front

    platforms = _normalize_platforms(args.platforms)
    if "xhs" in platforms:
        _start_browser_if_needed("xhs", 5003, "https://creator.xiaohongshu.com/creator/post")
    if "douyin" in platforms:
        _start_browser_if_needed("douyin", 5004, "https://creator.douyin.com/creator-micro/content/upload")
    if "bilibili" in platforms:
        _start_browser_if_needed("bilibili", 5005, "https://member.bilibili.com/platform/upload/video/frame")

    for platform in platforms:
        if platform == "xhs":
            bring_to_front(["小红书", "你访问的页面不见了"])
            XiaoHongShuLogin(create_new_driver(port=5003)).check_and_act()
        elif platform == "douyin":
            bring_to_front(["抖音"])
            DouyinLogin(create_new_driver(port=5004)).check_and_act()
        elif platform == "bilibili":
            bring_to_front(["哔哩哔哩", "bilibili", "Bilibili"])
            BilibiliLogin(create_new_driver(port=5005)).check_and_act()
        print(f"{platform}: login check completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
