"""Shipinhao music album (专辑 / zhuanji) management helpers.

The current Shipinhao desktop music flow creates/publishes a song through
``/platform/post/createMusic`` and requires album fields inside that same form.
The separate ``专辑`` screen under ``/platform/post/music`` is a management/list
tab, not a verified standalone album publish form. Keep this module
non-destructive until Shipinhao exposes a true album-only creation route.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from login_shipinhao import ShiPinHaoLogin
from pub_shipinhao_music import read_shipinhao_music_management


def _resolve_chromedriver_path() -> str:
    for key in ("AUTOPUBLISH_CHROMEDRIVER", "CHROMEDRIVER_PATH"):
        value = os.environ.get(key)
        if value and os.path.exists(value):
            return value
    for candidate in (
        "/usr/lib/chromium-browser/chromedriver",
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver",
    ):
        if os.path.exists(candidate):
            return candidate
    return "chromedriver"


def attach_driver(port: int = 5006):
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
    return webdriver.Chrome(service=Service(_resolve_chromedriver_path()), options=options)


class ShiPinHaoZhuanjiManager:
    """Read Shipinhao music album/song management tabs from the live browser."""

    def __init__(self, driver):
        self.driver = driver
        ShiPinHaoLogin(driver).check_and_act()

    def list_state(self) -> dict:
        return read_shipinhao_music_management(self.driver, tabs=("专辑", "音乐"))

    def list_albums(self) -> list[dict]:
        state = self.list_state()
        album_state = (state.get("tabs") or {}).get("专辑") or {}
        return album_state.get("rows") or []

    def list_music(self) -> list[dict]:
        state = self.list_state()
        music_state = (state.get("tabs") or {}).get("音乐") or {}
        return music_state.get("rows") or []


def main() -> int:
    os.environ.setdefault("DISPLAY", ":1")
    driver = attach_driver(port=int(os.environ.get("SHIPINHAO_PORT", "5006")))
    manager = ShiPinHaoZhuanjiManager(driver)
    payload = manager.list_state()
    output_path = Path(__file__).resolve().parent / "logs" / "shipinhao-zhuanji-management.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"Saved Shipinhao zhuanji management state to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
