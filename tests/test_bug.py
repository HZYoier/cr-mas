"""Bug 猎人测试"""

from pathlib import Path
from cr_mas.agents.bug import run

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_detects_type_error():
    """检测包含 str + int 的代码，应找到至少一个 TypeError bug"""
    file_path = str(FIXTURE_DIR / "buggy_code.py")
    result = run(file_path)

    bugs = result["bugs"]
    assert len(bugs) > 0, "应检测到至少一个 bug"

    for bug in bugs:
        assert "line" in bug
        assert bug["line"] > 0
        assert bug["severity"] in ("CRITICAL", "MEDIUM")
        assert "description" in bug
        assert "fix" in bug
