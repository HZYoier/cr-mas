from pathlib import Path
from cr_mas.agents.readability import run

FIXTURE_DIR = Path(__file__).parent / "fixtures"

def test_analyzes_readability():
    file_path = str(FIXTURE_DIR / "readability_code.py")
    result = run(file_path)

    metrics = result["metrics"]
    assert metrics["total_lines"] > 0
    assert metrics["function_count"] > 0
    assert metrics["max_function_lines"] > 0
    assert metrics["comment_ratio"] > 0

    functions = result["functions"]
    assert len(functions) == metrics["function_count"]
    for func in functions:
        assert "name" in func
        assert "line" in func
        assert "lines" in func
        assert func["lines"] > 0

