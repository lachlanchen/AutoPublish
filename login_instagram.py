import json
import os
import platform
import re
import socket
import subprocess
import time
import traceback
import urllib.request
import zipfile
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import SessionNotCreatedException

from utils import SendMail, dismiss_alert, bring_to_front


def _load_dotenv(env_path: Path):
    if not env_path.exists():
        return
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except Exception:
        traceback.print_exc()


def _is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def _resolve_chrome_bin():
    env_bin = os.getenv("INSTAGRAM_CHROME_BIN") or os.getenv("CHROME_BIN") or os.getenv("CHROMIUM_BIN")
    if env_bin:
        env_path = Path(env_bin)
        if env_path.exists():
            return str(env_path)
    machine = platform.machine().lower()
    prefer_chromium = machine.startswith("arm") or machine in {"aarch64", "arm64"}
    candidates = (
        ("chromium-browser", "chromium", "google-chrome", "google-chrome-stable")
        if prefer_chromium
        else ("google-chrome", "google-chrome-stable", "chromium-browser", "chromium")
    )
    for candidate in candidates:
        try:
            path = subprocess.check_output(f"command -v {candidate}", shell=True, text=True).strip()
        except Exception:
            continue
        if path:
            return path
    return "chromium-browser" if prefer_chromium else "google-chrome"


def _resolve_profile_dir(chrome_bin: str, port: int):
    env_dir = os.getenv("INSTAGRAM_PROFILE_DIR")
    if env_dir:
        return env_dir
    if "chromium" in chrome_bin:
        return str(Path.home() / f"chromium_dev_session_{port}")
    return str(Path.home() / f"chrome_dev_session_{port}")


def _resolve_logs_dir(chrome_bin: str):
    if "chromium" in chrome_bin:
        return str(Path.home() / "chromium_dev_session_logs")
    return str(Path.home() / "chrome_dev_session_logs")

def _resolve_display():
    env_display = os.getenv("INSTAGRAM_DISPLAY") or os.getenv("DISPLAY")
    if env_display:
        return env_display
    if Path("/tmp/.X11-unix/X1").exists():
        return ":1"
    if Path("/tmp/.X11-unix/X0").exists():
        return ":0"
    return ":0"

def _ensure_debug_chrome(port: int, chrome_bin: str | None = None):
    if _is_port_open("127.0.0.1", port):
        return

    chrome_bin = chrome_bin or _resolve_chrome_bin()
    profile_dir = _resolve_profile_dir(chrome_bin, port)
    logs_dir = _resolve_logs_dir(chrome_bin)
    log_path = Path(logs_dir) / "chrome_instagram.log"
    headless = os.getenv("INSTAGRAM_HEADLESS", "").strip().lower() in {"1", "true", "yes", "y"}

    Path(profile_dir).mkdir(parents=True, exist_ok=True)
    Path(logs_dir).mkdir(parents=True, exist_ok=True)

    display = _resolve_display()

    cmd = [
        chrome_bin,
        "--hide-crash-restore-bubble",
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "https://www.instagram.com",
    ]
    if headless:
        cmd.insert(1, "--headless=new")
        cmd.insert(2, "--disable-gpu")

    with open(log_path, "ab") as log_file:
        subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            env={**os.environ, "DISPLAY": display},
            start_new_session=True,
        )

    start_time = time.time()
    while time.time() - start_time < 15:
        if _is_port_open("127.0.0.1", port):
            return
        time.sleep(0.5)

def _detect_chrome_version():
    candidates = [
        "google-chrome --version",
        "google-chrome-stable --version",
        "chromium-browser --version",
        "chromium --version",
    ]
    for cmd in candidates:
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True).strip()
        except Exception:
            continue
        match = re.search(r"(\d+\.\d+\.\d+\.\d+)", output)
        if match:
            return match.group(1)
    return None


def _chromedriver_platform():
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "linux":
        if machine in {"aarch64", "arm64"}:
            return "linux-arm64"
        return "linux64"
    if system == "darwin":
        return "mac-arm64" if machine in {"arm64", "aarch64"} else "mac-x64"
    if system == "windows":
        return "win64"
    return None


def _download_chromedriver(version):
    platform_key = _chromedriver_platform()
    if not platform_key:
        return None
    cache_root = Path.home() / ".cache" / "chromedriver" / version / platform_key
    driver_path = cache_root / "chromedriver"
    if driver_path.exists():
        return str(driver_path)

    cache_root.mkdir(parents=True, exist_ok=True)
    index_url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
    with urllib.request.urlopen(index_url, timeout=20) as resp:
        payload = json.load(resp)

    versions = payload.get("versions", [])
    target = None
    major = version.split(".")[0] if version else None
    for item in reversed(versions):
        item_version = item.get("version", "")
        if major and not item_version.startswith(f"{major}."):
            continue
        downloads = item.get("downloads", {}).get("chromedriver", [])
        for entry in downloads:
            if entry.get("platform") == platform_key:
                target = entry.get("url")
                break
        if target:
            version = item_version
            break

    if not target:
        return None

    zip_path = cache_root / "chromedriver.zip"
    urllib.request.urlretrieve(target, zip_path)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(cache_root)
    zip_path.unlink(missing_ok=True)

    for child in cache_root.rglob("chromedriver"):
        child.chmod(0o755)
        return str(child)
    return None


def _candidate_driver_paths():
    paths = []
    candidates = [
        os.getenv("INSTAGRAM_CHROMEDRIVER_PATH"),
        os.getenv("CHROMEDRIVER_PATH"),
        "/usr/lib/chromium-browser/chromedriver",
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver",
        "/snap/bin/chromium.chromedriver",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            paths.append(candidate)
    try:
        resolved = subprocess.check_output("command -v chromedriver", shell=True, text=True).strip()
    except Exception:
        resolved = ""
    if resolved and Path(resolved).exists():
        paths.append(resolved)
    deduped = []
    seen = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        deduped.append(path)
    return deduped


def _build_driver(options, chrome_bin: str | None = None):
    last_exc = None
    if chrome_bin and Path(chrome_bin).exists():
        options.binary_location = chrome_bin
    for path in _candidate_driver_paths():
        try:
            return webdriver.Chrome(service=Service(path), options=options)
        except SessionNotCreatedException as exc:
            last_exc = exc
        except Exception as exc:
            last_exc = exc

    try:
        return webdriver.Chrome(options=options)
    except SessionNotCreatedException as exc:
        last_exc = exc

    chrome_version = _detect_chrome_version()
    if chrome_version:
        driver_path = _download_chromedriver(chrome_version)
        if driver_path:
            return webdriver.Chrome(service=Service(driver_path), options=options)

    if last_exc:
        raise last_exc
    return webdriver.Chrome(options=options)


class InstagramLogin:
    def __init__(self, driver=None, debug_port=None):
        print("Initializing InstagramLogin...")
        _load_dotenv(Path(__file__).resolve().parent / ".env")
        self.mailer = SendMail()
        self.debug_port = debug_port or int(os.getenv("INSTAGRAM_DEBUG_PORT", "5007"))
        self.driver = driver if driver else self.create_new_driver()

    def create_new_driver(self):
        print("Creating new WebDriver instance for Instagram...")
        options = webdriver.ChromeOptions()
        chrome_bin = _resolve_chrome_bin()
        _ensure_debug_chrome(self.debug_port, chrome_bin=chrome_bin)
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.debug_port}")
        driver = _build_driver(options, chrome_bin=chrome_bin)
        return driver

    def is_already_logged_in(self):
        driver = self.driver
        markers = [
            (By.XPATH, "//svg[@aria-label='New post']"),
            (By.XPATH, "//span[normalize-space()='Create']"),
            (By.XPATH, "//a[contains(@href, '/accounts/edit')]"),
        ]
        for by, value in markers:
            if driver.find_elements(by, value):
                return True
        return self.save_info_prompt_present()

    def save_info_prompt_present(self):
        driver = self.driver
        markers = [
            (By.XPATH, "//h1[normalize-space()='Save your login info?']"),
            (By.XPATH, "//div[@role='heading' and normalize-space()='Save your login info?']"),
            (By.XPATH, "//button[normalize-space()='Save info']"),
            (By.XPATH, "//div[@role='button' and normalize-space()='Not now']"),
        ]
        for by, value in markers:
            if driver.find_elements(by, value):
                return True
        return False

    def dismiss_save_info_prompt(self):
        driver = self.driver
        if not self.save_info_prompt_present():
            return False

        raw_pref = os.getenv("INSTAGRAM_SAVE_LOGIN")
        if raw_pref is None:
            save_login = True
        else:
            save_login = raw_pref.strip().lower() in {"1", "true", "yes", "y"}
        if save_login:
            button_order = ["Save info", "Not now"]
        else:
            button_order = ["Not now", "Save info"]

        for label in button_order:
            try:
                button = WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, f"//button[normalize-space()='{label}']"))
                )
                button.click()
                return True
            except Exception:
                pass

            try:
                button = WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, f"//div[@role='button' and normalize-space()='{label}']"))
                )
                button.click()
                return True
            except Exception:
                pass

        return False

    def is_login_form_visible(self):
        driver = self.driver
        return bool(driver.find_elements(By.NAME, "username")) and bool(
            driver.find_elements(By.NAME, "password")
        )

    def take_screenshot_and_send_email(self):
        screenshot_path = "/tmp/instagram-login.png"
        self.driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}.")
        self.mailer.send_email(
            "Instagram Login Required",
            "Login is required. Please see the attached screenshot.",
            screenshot_path,
            "instagram-login.png",
        )

    def try_password_login(self):
        username = os.getenv("IG_USERNAME") or os.getenv("INSTAGRAM_USERNAME")
        password = os.getenv("IG_PASSWORD") or os.getenv("INSTAGRAM_PASSWORD")
        if not username or not password:
            return False

        driver = self.driver
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, "username")))
            user_input = driver.find_element(By.NAME, "username")
            pass_input = driver.find_element(By.NAME, "password")
            user_input.click()
            user_input.send_keys(Keys.CONTROL, "a")
            user_input.send_keys(Keys.BACKSPACE)
            user_input.clear()
            user_input.send_keys(username)
            pass_input.click()
            pass_input.send_keys(Keys.CONTROL, "a")
            pass_input.send_keys(Keys.BACKSPACE)
            pass_input.clear()
            pass_input.send_keys(password)
            pass_input.send_keys(Keys.ENTER)
            return True
        except Exception:
            traceback.print_exc()
            return False

    def check_and_act(self):
        driver = self.driver
        print("Navigating to Instagram...")
        driver.get("https://www.instagram.com/")
        time.sleep(2)
        dismiss_alert(driver)
        time.sleep(2)
        bring_to_front(["Instagram"])

        if self.is_already_logged_in():
            print("Instagram already logged in.")
            self.dismiss_save_info_prompt()
            return

        try:
            WebDriverWait(driver, 15).until(
                lambda d: self.is_login_form_visible() or self.is_already_logged_in()
            )
        except Exception:
            print("Login form not detected yet.")

        if self.is_already_logged_in():
            print("Instagram logged in after page load.")
            self.dismiss_save_info_prompt()
            return

        if self.try_password_login():
            print("Submitted username/password. Waiting for login to complete.")
            time.sleep(5)
            if self.is_already_logged_in():
                print("Instagram login succeeded.")
                self.dismiss_save_info_prompt()
                return

        print("Instagram login requires manual action.")
        try:
            self.take_screenshot_and_send_email()
        except Exception:
            traceback.print_exc()

        start_time = time.time()
        while time.time() - start_time < 600:
            if self.is_already_logged_in():
                print("Instagram login completed.")
                self.dismiss_save_info_prompt()
                return
            time.sleep(5)

        print("Instagram login timed out.")


if __name__ == "__main__":
    InstagramLogin().check_and_act()
