"""Exercise name hints without importing a browser or sending login email."""
import ast
import os
from pathlib import Path
import pytest


@pytest.mark.parametrize('filename,prefix', [
    ('login_douyin.py', 'DOUYIN'),
    ('login_xiaohongshu.py', 'XHS'),
    ('login_bilibili.py', 'BILIBILI'),
])
def test_hosted_mode_does_not_expect_the_original_owners_name(monkeypatch, filename, prefix):
    tree = ast.parse((Path(__file__).parents[1] / filename).read_text())
    method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == '_expected_account_names')
    namespace = {'os': os}
    exec(compile(ast.Module(body=[method], type_ignores=[]), filename, 'exec'), namespace)
    monkeypatch.delenv(prefix+'_ACCOUNT_NAMES', raising=False)
    monkeypatch.delenv(prefix+'_ACCOUNT_NAME', raising=False)
    monkeypatch.setenv('AUTOPUBLISH_ACCOUNT_NEUTRAL', '1')
    assert namespace['_expected_account_names'](None) == []
    monkeypatch.setenv(prefix+'_ACCOUNT_NAME', 'Another creator')
    assert namespace['_expected_account_names'](None) == ['Another creator']
