import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.shipinhao_account_login import (
    PNG_SIGNATURE,
    QrState,
    isolated_profile_dir,
    matching_browser_process,
    safe_profile_name,
    validate_ports,
)


class IsolatedShipinhaoLoginTests(unittest.TestCase):
    def test_profile_name_is_filesystem_safe(self):
        self.assertEqual(safe_profile_name("波澜界 / test"), "test")
        with self.assertRaises(ValueError):
            safe_profile_name("中文")

    def test_only_named_isolated_profile_path_is_allowed(self):
        with tempfile.TemporaryDirectory() as home:
            expected = Path(home) / "chromium_dev_session_shipinhao_bolanjie"
            with patch.dict(os.environ, {"HOME": home}):
                with patch("pathlib.Path.home", return_value=Path(home)):
                    self.assertEqual(isolated_profile_dir("bolanjie"), expected)
                    self.assertEqual(
                        isolated_profile_dir("bolanjie", expected), expected
                    )
                    with self.assertRaises(ValueError):
                        isolated_profile_dir(
                            "bolanjie", Path(home) / "chromium_dev_session_5006"
                        )

    def test_legacy_ports_are_reserved(self):
        for port in (5003, 5004, 5005, 5006, 5007, 9222):
            with self.subTest(port=port), self.assertRaises(ValueError):
                validate_ports(port, 8765)
        with self.assertRaises(ValueError):
            validate_ports(5016, 5016)
        validate_ports(5016, 8765)

    def test_browser_match_checks_all_chromium_children(self):
        with tempfile.TemporaryDirectory() as directory:
            proc_root = Path(directory)
            wrong = proc_root / "10"
            correct = proc_root / "20"
            wrong.mkdir()
            correct.mkdir()
            port = b"--remote-debugging-port=5016"
            profile = Path("/tmp/chromium_dev_session_shipinhao_bolanjie")
            (wrong / "cmdline").write_bytes(
                b"chromium\0" + port + b"\0--type=renderer\0"
            )
            (correct / "cmdline").write_bytes(
                b"chromium --type=renderer "
                + port
                + b" --user-data-dir="
                + str(profile).encode()
                + b" https://channels.weixin.qq.com/\0"
            )
            self.assertTrue(matching_browser_process(5016, profile, proc_root))

    def test_browser_match_rejects_profile_prefix_collision(self):
        with tempfile.TemporaryDirectory() as directory:
            proc_root = Path(directory)
            process = proc_root / "10"
            process.mkdir()
            profile = Path("/tmp/chromium_dev_session_shipinhao_bolanjie")
            (process / "cmdline").write_bytes(
                b"chromium --remote-debugging-port=5016 "
                b"--user-data-dir=/tmp/chromium_dev_session_shipinhao_bolanjie-other\0"
            )
            self.assertFalse(matching_browser_process(5016, profile, proc_root))

    def test_qr_state_versions_changes_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            state = QrState(root / "state", "bolanjie")
            source.write_bytes(PNG_SIGNATURE + b"first")
            state.require(str(source), "scan")
            self.assertEqual(state.snapshot()["revision"], 1)
            state.require(str(source), "scan")
            self.assertEqual(state.snapshot()["revision"], 1)
            source.write_bytes(PNG_SIGNATURE + b"second")
            state.require(str(source), "scan")
            self.assertEqual(state.snapshot()["revision"], 2)
            self.assertEqual(state.qr_bytes(), PNG_SIGNATURE + b"second")


if __name__ == "__main__":
    unittest.main()
