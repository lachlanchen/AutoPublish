import tempfile
import unittest
from pathlib import Path

from publish_attention import PublishAttentionRegistry


PNG = b"\x89PNG\r\n\x1a\n" + b"test-png"


class PublishAttentionRegistryTests(unittest.TestCase):
    def test_required_attention_is_versioned_and_resolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "qr.png"
            source.write_bytes(PNG)
            registry = PublishAttentionRegistry(Path(tmp) / "registry")

            first = registry.require(
                "job-1",
                platform="shipinhao",
                kind="login_qr",
                artifact_path=source,
                message="scan",
            )
            duplicate = registry.require(
                "job-1",
                platform="shipinhao",
                kind="login_qr",
                artifact_path=source,
                message="scan",
            )

            self.assertEqual(first["revision"], 1)
            self.assertEqual(duplicate["revision"], 1)
            self.assertEqual(first["status"], "required")
            self.assertEqual(
                first["artifact_url"],
                "/publish/jobs/job-1/attention/1",
            )
            artifact = registry.artifact("job-1", 1)
            self.assertIsNotNone(artifact)
            self.assertEqual(artifact[0].read_bytes(), PNG)

            resolved = registry.resolve(
                "job-1",
                platform="shipinhao",
                kind="login_qr",
            )
            self.assertEqual(resolved["status"], "resolved")
            self.assertNotIn("artifact_url", resolved)
            self.assertIsNone(registry.artifact("job-1", 1))

    def test_changed_qr_increments_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "qr.png"
            registry = PublishAttentionRegistry(Path(tmp) / "registry")
            source.write_bytes(PNG + b"-one")
            registry.require(
                "job-2",
                platform="shipinhao",
                kind="login_qr",
                artifact_path=source,
                message="scan",
            )
            source.write_bytes(PNG + b"-two")
            refreshed = registry.require(
                "job-2",
                platform="shipinhao",
                kind="login_qr",
                artifact_path=source,
                message="scan",
            )
            self.assertEqual(refreshed["revision"], 2)
            self.assertIsNone(registry.artifact("job-2", 1))
            self.assertIsNotNone(registry.artifact("job-2", 2))


if __name__ == "__main__":
    unittest.main()
