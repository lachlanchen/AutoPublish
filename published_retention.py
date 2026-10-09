"""Remove verified publication staging media, never sources or browser profiles."""
import argparse
import hashlib
import json
from pathlib import Path
import stat
import time
import zipfile

from queue_journal import QueueJournal


PLATFORMS = {
    'xiaohongshu': 'XiaoHongShu', 'douyin': 'Douyin', 'bilibili': 'Bilibili',
    'shipinhao': 'ShiPinHao', 'shipinhao_music': 'ShiPinHaoMusic',
    'youtube_music': 'YouTubeMusic', 'bandcamp_music': 'BandcampMusic',
    'youtube': 'YouTube', 'instagram': 'Instagram',
}
MEDIA_SUFFIXES = {'.mp4', '.mov', '.webm', '.mkv', '.mp3', '.wav', '.flac',
                  '.m4a', '.aac', '.ogg'}


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _regular_file(path, directory):
    # Reject symlinks at every level, including links within the package tree.
    try:
        parts = path.relative_to(directory).parts
        current = directory
        for part in parts:
            current = current / part
            if current.is_symlink():
                return False
        return stat.S_ISREG(path.lstat().st_mode)
    except (ValueError, OSError):
        return False


def cleanup_published(jobs, root, *, apply=False):
    """Caller must serialize with queue acceptance; uncertain packages are kept.

    A scoped retry may complete a partial batch. All requested targets across
    the same immutable archive must then have a successful receipt. Any active
    job for the basename blocks cleanup, even if its archive hash differs.
    """
    root = Path(root).resolve()
    reports = []
    for filename in sorted({j.get('filename', '') for j in jobs}):
        if not filename or Path(filename).name != filename or not filename.endswith('.zip'):
            continue
        related = [j for j in jobs if j.get('filename') == filename]
        if any(j.get('status') not in {'done', 'failed'} for j in related):
            continue
        directory = root / Path(filename).stem
        package = directory / filename
        if directory.is_symlink() or not _regular_file(package, directory):
            continue
        digest = sha256(package)
        matching = [j for j in related if j.get('package_sha256') == digest]
        if not matching or any(j.get('local_package') or j.get('test_mode') for j in matching):
            continue
        if any(Path(j.get('zip_path', '')).absolute() != package
               or Path(j.get('transcription_dir', '')).absolute() != directory
               for j in matching):
            continue
        requested = set().union(*(set(j.get('platforms', [])) for j in matching))
        if not requested or not requested <= PLATFORMS.keys():
            continue
        completed = {p for p in requested if any(
            j.get('platform_results', {}).get(PLATFORMS[p], {}).get('status') == 'done'
            for j in matching)}
        if completed != requested:
            continue
        # Keep metadata, corrected lyrics, subtitle files, proofs and receipts.
        # Remove only media known to have come from this exact uploaded archive.
        files = []
        with zipfile.ZipFile(package) as archive:
            for member in archive.infolist():
                rel = Path(member.filename)
                if rel.is_absolute() or '..' in rel.parts:
                    raise ValueError('Unsafe archive member in published package')
                target = directory / rel
                if rel.suffix.lower() in MEDIA_SUFFIXES and _regular_file(target, directory):
                    with archive.open(member) as stream:
                        member_digest = hashlib.sha256()
                        for block in iter(lambda: stream.read(1024 * 1024), b''):
                            member_digest.update(block)
                    if sha256(target) == member_digest.hexdigest():
                        files.append(target)
        files = list(dict.fromkeys(files)) + [package]
        report = {
            'filename': filename, 'package_sha256': digest,
            'job_ids': [j['id'] for j in matching],
            'platforms': sorted(completed),
            'platform_results': {j['id']: j.get('platform_results', {}) for j in matching},
            'files': [{'path': str(p.relative_to(root)), 'bytes': p.stat().st_size,
                       'sha256': sha256(p)} for p in files],
            'created_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'status': 'planned',
        }
        if apply:
            # Durable evidence precedes deletion. A cleanup failure must never
            # turn a successful publication into a failed/retried publication.
            receipt = root / '.published-receipts' / f'{digest}.json'
            journal = QueueJournal(receipt)
            journal.save([report])
            for entry, path in zip(report['files'], files):
                if not _regular_file(path, directory) or sha256(path) != entry['sha256']:
                    raise ValueError('Staging file changed during cleanup; stopped')
                path.unlink()
            report['status'] = 'removed'
            journal.save([report])
        reports.append(report)
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--journal', required=True)
    parser.add_argument('--root', required=True)
    parser.add_argument('--apply', action='store_true', help='Only with an idle/stopped publisher')
    args = parser.parse_args()
    # Read without QueueJournal.restore(), which changes interrupted job states.
    jobs = json.loads(Path(args.journal).read_text())['jobs']
    if args.apply and any(j.get('status') in {'queued', 'running'} for j in jobs):
        parser.error('Wait for the publisher queue to become idle before offline cleanup')
    print(json.dumps(cleanup_published(jobs, args.root, apply=args.apply), indent=2))


if __name__ == '__main__':
    main()
