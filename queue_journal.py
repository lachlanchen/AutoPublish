"""Optional durable queue; never replay a possibly submitted publication."""
import json
import os
from pathlib import Path


class QueueJournal:
    def __init__(self, path=None):
        self.path = Path(path) if path else None

    def save(self, jobs):
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix('.tmp')
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump({'version': 1, 'jobs': jobs}, stream, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, self.path)
        directory = os.open(self.path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)

    def restore(self):
        if not self.path or not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding='utf-8'))
        if data.get('version') != 1 or not isinstance(data.get('jobs'), list):
            raise ValueError('Invalid publish queue journal; operator recovery required')
        jobs = data['jobs']
        for job in jobs:
            if job['status'] == 'running':
                job['status'] = 'failed'
                job['error'] = ('Publisher restarted during submission. Check platform history '
                                'before retrying; this job was NOT automatically replayed.')
        self.save(jobs)
        return jobs
