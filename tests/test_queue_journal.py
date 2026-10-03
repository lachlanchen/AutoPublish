import json
import stat
from queue_journal import QueueJournal


def test_restart_keeps_queued_and_completed_but_fences_uncertain_submission(tmp_path):
    path = tmp_path / 'queue.json'
    journal = QueueJournal(path)
    journal.save([{'id': str(i), 'status': status} for i, status in
                  enumerate(['queued', 'running', 'done', 'failed'])])
    restored = QueueJournal(path).restore()
    assert [r['status'] for r in restored] == ['queued', 'failed', 'done', 'failed']
    assert 'NOT automatically replayed' in restored[1]['error']
    assert json.loads(path.read_text())['jobs'] == restored
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_disabled_journal_has_no_runtime_effect():
    journal = QueueJournal()
    journal.save([{'id': 'x', 'status': 'queued'}])
    assert journal.restore() == []


def test_corrupt_journal_fails_closed(tmp_path):
    import pytest
    path = tmp_path / 'queue.json'
    path.write_text('{broken')
    with pytest.raises(ValueError):
        QueueJournal(path).restore()


def test_history_limit_never_evicts_waiting_jobs(tmp_path):
    import ast
    import queue
    import threading
    from pathlib import Path
    # Use the real queue entry point without importing Selenium/login modules.
    source = ast.parse((Path(__file__).parents[1] / 'app.py').read_text())
    enqueue = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == '_enqueue_publish_job')
    context = {'PUBLISH_LOCK': threading.Lock(), 'PUBLISH_JOBS': {},
               'PUBLISH_JOB_ORDER': [], 'PUBLISH_MAX_HISTORY': 2,
               'PUBLISH_QUEUE': queue.Queue(), 'PUBLISH_JOURNAL': QueueJournal(tmp_path / 'queue.json')}
    exec(compile(ast.Module(body=[enqueue], type_ignores=[]), 'app.py', 'exec'), context)
    for i in range(5):
        context['_enqueue_publish_job']({'id': str(i), 'status': 'queued'})
    for i in range(5, 9):
        context['_enqueue_publish_job']({'id': str(i), 'status': 'done'})
    restored = context['PUBLISH_JOURNAL'].restore()
    assert [j['id'] for j in restored if j['status'] == 'queued'] == ['0', '1', '2', '3', '4']
    assert len([j for j in restored if j['status'] == 'done']) == 2
