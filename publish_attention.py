"""Thread-safe, job-scoped human-attention artifacts for AutoPublish."""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_ATTENTION_ARTIFACT_BYTES = 5 * 1024 * 1024


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_component(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value or "")).strip("-.")
    return cleaned[:120] or "unknown"


class PublishAttentionRegistry:
    """Own the latest operator-attention event for each publish job."""

    def __init__(self, root: str | Path | None = None):
        configured_root = root or os.environ.get("AUTOPUBLISH_ATTENTION_DIR")
        self.root = Path(
            configured_root
            or Path(tempfile.gettempdir()) / "autopublish-attention"
        ).expanduser()
        self._lock = threading.Lock()
        self._events: dict[str, dict] = {}

    def require(
        self,
        job_id: str,
        *,
        platform: str,
        kind: str,
        artifact_path: str | Path,
        message: str,
    ) -> dict:
        source = Path(artifact_path)
        data = source.read_bytes()
        if not data.startswith(PNG_SIGNATURE):
            raise ValueError("attention artifact must be a PNG")
        if len(data) > MAX_ATTENTION_ARTIFACT_BYTES:
            raise ValueError("attention artifact exceeds the size limit")

        digest = hashlib.sha256(data).hexdigest()
        job_key = str(job_id)
        now = _timestamp()
        with self._lock:
            previous = self._events.get(job_key)
            if (
                previous
                and previous.get("status") == "required"
                and previous.get("platform") == platform
                and previous.get("kind") == kind
                and previous.get("sha256") == digest
            ):
                return self._public_event(previous)

            revision = int((previous or {}).get("revision") or 0) + 1
            destination_dir = self.root / _safe_component(job_key)
            destination_dir.mkdir(parents=True, exist_ok=True)
            destination = destination_dir / (
                f"{_safe_component(platform)}-{_safe_component(kind)}-r{revision}.png"
            )
            temporary = destination.with_suffix(".tmp")
            temporary.write_bytes(data)
            os.replace(temporary, destination)

            if previous:
                old_path = Path(str(previous.get("artifact_path") or ""))
                if old_path and old_path != destination:
                    try:
                        old_path.unlink(missing_ok=True)
                    except OSError:
                        pass

            event = {
                "job_id": job_key,
                "platform": str(platform),
                "kind": str(kind),
                "status": "required",
                "message": str(message),
                "revision": revision,
                "created_at": (previous or {}).get("created_at") or now,
                "updated_at": now,
                "sha256": digest,
                "artifact_path": str(destination),
                "media_type": "image/png",
            }
            self._events[job_key] = event
            return self._public_event(event)

    def resolve(
        self,
        job_id: str,
        *,
        platform: str | None = None,
        kind: str | None = None,
    ) -> dict | None:
        job_key = str(job_id)
        with self._lock:
            event = self._events.get(job_key)
            if not event:
                return None
            if platform and event.get("platform") != platform:
                return None
            if kind and event.get("kind") != kind:
                return None
            event["status"] = "resolved"
            event["updated_at"] = _timestamp()
            return self._public_event(event)

    def public(self, job_id: str) -> dict | None:
        with self._lock:
            event = self._events.get(str(job_id))
            return self._public_event(event) if event else None

    def artifact(self, job_id: str, revision: int) -> tuple[Path, str] | None:
        with self._lock:
            event = self._events.get(str(job_id))
            if (
                not event
                or event.get("status") != "required"
                or int(event.get("revision") or 0) != int(revision)
            ):
                return None
            path = Path(str(event.get("artifact_path") or ""))
            media_type = str(event.get("media_type") or "application/octet-stream")
        if not path.is_file():
            return None
        return path, media_type

    @staticmethod
    def _public_event(event: dict) -> dict:
        payload = {
            key: event.get(key)
            for key in (
                "platform",
                "kind",
                "status",
                "message",
                "revision",
                "created_at",
                "updated_at",
                "media_type",
            )
        }
        if event.get("status") == "required":
            job_id = quote(str(event.get("job_id") or ""), safe="")
            payload["artifact_url"] = (
                f"/publish/jobs/{job_id}/attention/{int(event.get('revision') or 0)}"
            )
        return payload
