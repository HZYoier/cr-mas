from pathlib import Path
from cr_mas.agents.style import run as style_run

FIXTURE_DIR = Path(__file__).parent / "fixtures"

def test_style_run():
    file_path = str(FIXTURE_DIR / "bad_style.py")
    result = style_run(file_path)

    assert result["agent"] == "Style"
    assert isinstance(result["issues"], list)
    assert result["summary"]["total"] == len(result["issues"])

    if result["issues"]:
        issue = result["issues"][0]
        assert isinstance(issue["file"], str)
        assert isinstance(issue["line"], int)
        assert isinstance(issue["col"], int)
        assert isinstance(issue["rule_id"], str)
        assert isinstance(issue["desc"], str)

        rule_first_char = issue["rule_id"][0]
        assert rule_first_char in ("E", "F", "W", "N", "B", "D")


        