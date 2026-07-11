"""SQLite 数据库访问层——所有记忆读写走这里"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "cr_mas_memory.db"

def _get_conn() -> sqlite3.Connection:
    # 连接数据库，自动建表
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    #首次自动建表
    schema = Path(__file__).parent / "schema.sql"
    conn.executescript(schema.read_text(encoding = "utf-8"))
    return conn


def save_review(state: dict) -> int:
    """
    将一次审查的完整 State 写入数据库
    返回新记录的 id
    """
    conn = _get_conn()

    final = state.get("final_report", {})
    changed_files = json.dumps(state.get("changed_files", []), ensure_ascii = False)
    verdict_json = json.dumps(final, ensure_ascii = False)
    react_trace = json.dumps(state.get("react_trace", []), ensure_ascii = False)

    summary = final.get("summary", {})

    cursor = conn.execute(
        """INSERT INTO review_records
           (commit_hash, module, changed_files, total_issues,
            critical_count, verdict_json, react_trace)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            state.get("commit_hash", ""),
            "",
            changed_files,
            summary.get("total", 0),
            summary.get("critical", 0),
            verdict_json,
            react_trace,
        )
    )

    conn.commit()
    return cursor.lastrowid


def get_review_history(limit: int = 10) -> list[dict]:
    """
    获取最近 N 次审查记录，按时间倒序
    """
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM review_records ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    return [dict(row) for row in rows]


def get_agent_accuracy(module: str = "") -> list[dict]:
    """
    查询各 Agent 在某模块的建议采纳率
    """
    conn = _get_conn()
    if module:
        rows = conn.exeute(
            "SELECT * FROM agent_accuracy WHERE module = ?",
            (module,)
        ).fetchall()
    else:
        # 返回所有模块的统计
        rows = conn.execute(
            "SELECT * FROM agent_accuracy"
        ).fetchall()
    return [dict(row) for row in rows]
