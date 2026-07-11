from pathlib import Path
from cr_mas.agents.security import run

FIXTUR_DIR = Path(__file__).parent / "fixtures"


def test_detects_sql_injection():
    file_path = str(FIXTUR_DIR / "sql_injection.py")
    result = run(file_path)

    alerts = result["alerts"]
    assert len(alerts) > 0

    for alert in alerts:
        assert "file" in alert
        assert "line" in alert
        assert alert["line"] > 0
        assert "risk_type" in alert
        assert alert["severity"] in ["CRITICAL", "MEDIUM"]
        assert "description" in alert