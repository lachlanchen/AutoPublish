"""Validate uploads before replacing an archive used by a publication job."""
import hashlib
import io
import os
from pathlib import Path, PurePosixPath
import tempfile
import zipfile
import zlib

from local_package import checksum


def extracted_members_current(zip_path, extract_dir):
    root = Path(extract_dir).resolve()
    try:
        with zipfile.ZipFile(zip_path) as archive:
            members = [item for item in archive.infolist() if not item.is_dir()]
        if not members:
            return False
        for member in members:
            path = (root / member.filename).resolve()
            if not path.is_relative_to(root) or path.stat().st_size != member.file_size:
                return False
            crc = 0
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    crc = zlib.crc32(block, crc)
            if crc != member.CRC:
                return False
        return True
    except (OSError, zipfile.BadZipFile):
        return False


def validate_archive(source):
    try:
        with zipfile.ZipFile(source) as archive:
            if not any(not member.is_dir() for member in archive.infolist()):
                raise ValueError("Publication ZIP is empty")
            for member in archive.infolist():
                path = PurePosixPath(member.filename.replace("\\", "/"))
                if path.is_absolute() or ".." in path.parts:
                    raise ValueError("Publication ZIP has an unsafe member path")
            if archive.testzip() is not None:
                raise ValueError("Publication ZIP failed CRC validation")
    except (zipfile.BadZipFile, EOFError, RuntimeError) as exc:
        raise ValueError("Invalid publication ZIP; send raw ZIP bytes or use reuse_existing=true") from exc


def store_publish_package(path, content, *, reuse_existing=False, allow_replace=True):
    target = Path(path)
    if reuse_existing:
        if not target.is_file():
            raise ValueError("reuse_existing requested but publication ZIP does not exist")
        validate_archive(target)
        return checksum(target)
    if not content or not zipfile.is_zipfile(io.BytesIO(content)):
        raise ValueError("Expected raw ZIP bytes; for an existing package use reuse_existing=true")
    validate_archive(io.BytesIO(content))
    digest = hashlib.sha256(content).hexdigest()
    if target.is_file() and checksum(target) == digest:
        return digest
    if not allow_replace:
        raise FileExistsError("Package is used by a queued/running job; retry after it finishes")
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=target.name + ".tmp-", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return digest
