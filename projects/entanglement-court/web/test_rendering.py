"""Quick JS renderer and syntax regression checks, invoked by pytest."""
import shutil
import subprocess
import tempfile
from pathlib import Path
import pytest

WEB = Path(__file__).parent


def test_renderer_regressions():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is required for renderer checks')
    result = subprocess.run([node, str(WEB / 'test_renderer.cjs')], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_main_js_syntax_on_module_copy():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is required for syntax checks')
    with tempfile.TemporaryDirectory(dir=WEB) as temporary:
        module = Path(temporary) / 'main.mjs'
        module.write_bytes((WEB / 'main.js').read_bytes())
        result = subprocess.run([node, '--check', str(module)], capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr


def test_web_sources_are_utf8_without_bom():
    for path in WEB.iterdir():
        if path.suffix in ('.py', '.js', '.css', '.html', '.cjs'):
            raw = path.read_bytes()
            assert not raw.startswith(b'\xef\xbb\xbf'), str(path)
            raw.decode('utf-8')
