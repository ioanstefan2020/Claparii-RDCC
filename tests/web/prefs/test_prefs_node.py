"""Pytest runner bridge for Preferences Engine Node.js test suite (owner: p2)."""
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEST_MJS = Path(__file__).resolve().parent / "test_prefs.mjs"


def test_prefs_engine_node_suite():
    """Run preferences engine unit test suite using Node.js built-in test runner."""
    assert shutil.which("node") is not None, "Node.js (>=18) is required to run web unit tests"
    assert TEST_MJS.exists(), f"Test file not found: {TEST_MJS}"
    res = subprocess.run(
        ["node", "--test", str(TEST_MJS)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, (
        f"Node preferences tests failed (exit code {res.returncode}):\n"
        f"STDOUT:\n{res.stdout}\n"
        f"STDERR:\n{res.stderr}"
    )

