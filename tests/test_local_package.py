"""Shared-volume delivery must not duplicate media or clean canonical files."""
import ast
import hashlib
import io
import json
import os
import queue
import tempfile
import threading
import zipfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

import pytest
import tornado.web
import tornado.testing

from local_package import checksum, clean_scratch, resolve_package
from publish_package import store_publish_package, validate_archive


def valid_zip(text='reviewed metadata'):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        archive.writestr('video_metadata.json', text)
    return stream.getvalue()


def test_resolve_requires_opt_in_loopback_and_real_workspace_path(tmp_path):
    root = tmp_path / 'data'
    root.mkdir()
    package = root / 'video.zip'
    package.write_bytes(b'canonical archive')
    path, digest = resolve_package(package, root, '127.0.0.1')
    assert path == str(package)
    assert digest == hashlib.sha256(package.read_bytes()).hexdigest()
    package.write_bytes(b'replaced after queueing')
    assert checksum(path) != digest
    outside = tmp_path / 'outside.zip'
    outside.write_bytes(b'private')
    link = root / 'escape.zip'
    link.symlink_to(outside)
    for target, allowed, ip in [(package, None, '127.0.0.1'),
                                (package, root, '192.0.2.1'),
                                (link, root, '127.0.0.1'),
                                (outside, root, '::1')]:
        with pytest.raises(ValueError):
            resolve_package(target, allowed, ip)


def test_cleanup_only_disposable_job_scratch(tmp_path):
    package = tmp_path / 'canonical.zip'
    package.write_bytes(b'keep')
    root = tmp_path / 'scratch'
    scratch = root / 'job-1'
    scratch.mkdir(parents=True)
    (scratch / 'extracted.mp4').write_bytes(b'temporary')
    job = {'id': 'job-1', 'local_package': True,
           'zip_path': str(package), 'transcription_dir': str(scratch)}
    clean_scratch({**job, 'local_package': False}, root)
    assert scratch.exists(), 'legacy deployment must not change'
    with pytest.raises(ValueError):
        clean_scratch({**job, 'transcription_dir': str(tmp_path)}, root)
    with pytest.raises(ValueError):
        clean_scratch({**job, 'zip_path': str(scratch / 'keep.zip')}, root)
    clean_scratch(job, root)
    clean_scratch(job, root)  # Restart recovery is idempotent.
    assert not scratch.exists()
    assert package.read_bytes() == b'keep'


class TestLocalPackageEndpoint(tornado.testing.AsyncHTTPTestCase):
    """Exercise the real handler without starting browsers or a queue worker."""
    def runTest(self):
        # Older pytest versions instantiate unittest cases during collection.
        pass

    def setUp(self):
        self.storage = tempfile.TemporaryDirectory()
        self.root = Path(self.storage.name)
        self.jobs = []
        self.registry = {}
        self.environment = patch.dict(os.environ, {'AUTOPUBLISH_LOCAL_PACKAGE_ROOT': str(self.root / 'data')})
        self.environment.start()
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.environment.stop()
        self.storage.cleanup()

    def get_app(self):
        source = ast.parse((Path(__file__).parents[1] / 'app.py').read_text())
        names = {'PublishHandler', '_parse_bool_arg', '_parse_restart_platforms',
                 '_normalize_platform_name'}
        nodes = [n for n in source.body if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name in names]
        context = {'tornado': __import__('tornado'), 'asyncio': __import__('asyncio'), 'os': os, 'Path': Path,
                   'datetime': datetime, 'json': json, 'time': __import__('time'),
                   're': __import__('re'), 'PLATFORM_ALIASES': {},
                   'resolve_package': resolve_package, '_new_job_id': lambda: 'job-1',
                   'store_publish_package': store_publish_package, 'validate_archive': validate_archive,
                   'PUBLISH_LOCK': threading.Lock(), 'PUBLISH_JOBS': self.registry,
                   '_enqueue_publish_job': self.jobs.append, 'PUBLISH_QUEUE': queue.Queue(),
                   '_job_timestamp': lambda: 'test'}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), 'app.py', 'exec'), context)
        return tornado.web.Application([(r'/publish', context['PublishHandler'],
                                        {'transcription_root': str(self.root / 'publisher'), 'chromedriver_path': ''})])

    def test_local_delivery_keeps_one_archive(self):
        package = self.root / 'data' / 'video.zip'
        package.parent.mkdir()
        package.write_bytes(valid_zip())
        response = self.fetch('/publish?' + urlencode({'filename': 'video.zip', 'local_package': str(package)}),
                              method='POST', body=b'')
        assert response.code == 200
        assert self.jobs[0]['zip_path'] == str(package)
        assert self.jobs[0]['local_package'] is True
        assert list(self.root.rglob('*.zip')) == [package]
        assert not (self.root / 'publisher' / 'video').exists()

    def test_remote_body_delivery_still_works(self):
        body = valid_zip()
        response = self.fetch('/publish?filename=video.zip', method='POST', body=body)
        assert response.code == 200
        assert self.jobs[0]['local_package'] is False
        assert Path(self.jobs[0]['zip_path']).read_bytes() == body
        assert self.jobs[0]['package_sha256'] == hashlib.sha256(body).hexdigest()

    def test_malformed_retry_is_400_without_overwriting_or_queueing(self):
        package = self.root / 'publisher' / 'video' / 'video.zip'
        package.parent.mkdir(parents=True)
        package.write_bytes(valid_zip())
        before = package.read_bytes()
        response = self.fetch('/publish?filename=video.zip', method='POST', body=b'--multipart-fields-only')
        assert response.code == 400
        assert not self.jobs
        assert package.read_bytes() == before

    def test_replacing_active_job_package_is_409(self):
        package = self.root / 'publisher' / 'video' / 'video.zip'
        package.parent.mkdir(parents=True)
        package.write_bytes(valid_zip())
        self.registry['existing'] = {'zip_path': str(package), 'status': 'running'}
        response = self.fetch('/publish?filename=video.zip', method='POST', body=valid_zip('new metadata'))
        assert response.code == 409
        assert not self.jobs
        assert package.read_bytes() == valid_zip()
