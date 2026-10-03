"""Read a canonical ZIP from shared workspace storage; clean only its scratch."""
import hashlib
import shutil
from pathlib import Path


def checksum(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def resolve_package(path, root, remote_ip):
    if not root or remote_ip not in {'127.0.0.1', '::1'}:
        raise ValueError('Local packages require the private loopback publisher')
    package, directory = Path(path).resolve(), Path(root).resolve()
    if not package.is_relative_to(directory) or not package.is_file() or package.suffix.lower() != '.zip':
        raise ValueError('Package is outside the configured workspace')
    return str(package), checksum(package)


def clean_scratch(job, scratch_root):
    if not job.get('local_package'):
        return
    directory = Path(job['transcription_dir']).resolve()
    root = Path(scratch_root).resolve()
    package = Path(job['zip_path']).resolve()
    # Canonical archive, user uploads and logs are NEVER scratch.
    if directory.parent != root or directory.name != job['id'] or package.is_relative_to(directory):
        raise ValueError('Refusing to clean an unexpected publication directory')
    shutil.rmtree(directory, ignore_errors=True)
