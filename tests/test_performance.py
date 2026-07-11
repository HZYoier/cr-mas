from pathlib import Path
from cr_mas.agents.performance import run

FIXTURES_DIR = Path(__file__).parent / "fixtures"
def test_analyzes_complexity():
    file_path = str(FIXTURES_DIR / "complex_function.py")
    result = run(file_path)

    metrics = result["metrics"]
    assert metrics["cyclomatic_complexity"] > 0
    assert metrics["nesting_depth"] >= 2
    assert isinstance(result["hotspot_details"], list)


def test_no_hotspots():
    "无高风险行时，热点列表为空"
    file_path = str(FIXTURES_DIR / "complex_function.py")
    result = run(file_path, hot_lines = None)
    assert result["hotspot_details"] == []
