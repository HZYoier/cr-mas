"""风格警察"""
import subprocess
import json
from cr_mas.graph.state import ReviewState
from cr_mas.llm.client import parse_llm_json
import sqlite3
from pathlib import Path
import re

# 正则匹配
_FUZZY_RULES = [
    (r"'.+' imported but unused", "导入但未使用"),
    (r"undefined name'.*'", "变量未定义"),
    (r"expected \d+ blank lines?.*found \d+", "空行数量不符合规范"),
    (r"too many blank lines \(\d+\)", "连续空行过多"),

]

def _fuzzy_translate(text):
    for pattern, zh in _FUZZY_RULES:
        m = re.match(pattern, text)
        if m:
            return f"{m.group(0)}（{zh}）" 
    return None

# flake8 常用翻译表
STYLE_TRANSLATIONS = {
    "missing whitespace around operator": "运算符缺少空格",
    "imported but unused": "导入但未使用",
    "module level import not at top of file": "import 语句未放在文件顶部",
    "multiple imports on one line": "一行内导入多个模块",
    "expected 2 blank lines, found 1": "函数定义前需要 2 个空行",
    "expected 2 blank lines, found 0": "函数定义前需要 2 个空行",
    "expected 1 blank line, found 0": "函数之间需要 1 个空行",
    "line too long": "单行过长",
    "trailing whitespace": "行末多余空格",
    "blank line contains whitespace": "空行包含不可见空格",
    "local variable is assigned to but never used": "变量已赋值但从未使用",
    "undefined name": "变量未定义",
    "unexpected spaces around keyword / parameter equals": "关键字参数等号周围有多余空格",
    "missing whitespace after ','": "逗号后缺少空格",
    "too many blank lines": "连续空行过多",
    "no newline at end of file": "文件末尾缺少换行符"
}



def _load_translations():
    # 从数据库加载已有翻译
    db = Path(__file__).parent.parent.parent / "cr_mas_memory.db"
    try:
        conn = sqlite3.connect(str(db))
        rows = conn.execute("SELECT en, zh FROM style_translations").fetchall()
        for en, zh in rows:
            STYLE_TRANSLATIONS[en] = zh
        conn.close()
    except Exception:
        pass


def _save_translations(new: dict):
    # 将新翻译写入数据库
    db = Path(__file__).parent.parent.parent / "cr_mas_memory.db"
    try:
        conn = sqlite3.connect(str(db))
        for en, zh in new.items():
            conn.execute(
                "INSERT OR IGNORE INFO style_translations (en, zh) VALUE (?, ?)",
                (en, zh)
            )
            conn.commit() # 写入磁盘
            conn.close()
    except Exception:
        pass


# 未翻译的新词收集器（每个 Agent 运行期间自动累积）
_missing = set()

def run(file_path: str) -> dict:
    """
    对单个文件运行 flake8，返回标准化的问题列表
    参数:
        file_path: 要检查的 Python 文件路径
    返回:
        {"issues": [...], "summary": {...}}
    """
    result = subprocess.run(["flake8", "--format=json", file_path], capture_output = True, text = True)
    issues = []
    if result.stdout.strip():
        file_issues = json.loads(result.stdout).get(file_path, [])
        for v in file_issues:
            if v["code"] == "E999":
                continue

            
            desc = STYLE_TRANSLATIONS.get(v["text"]) or _fuzzy_translate(v["text"])
            if desc is None:
                desc = v["text"] 
                _missing.add(v["text"])

            issues.append({
                "file": file_path,
                "line": v["line_number"],
                "col": v["column_number"],
                "rule_id": v["code"],
                "desc": desc,
            })


    return {
        "agent": "Style",
        "issues": issues,
        "summary": {"total": len(issues)},
    }
    

def review_node(state: ReviewState) -> dict:
    # 遍历变更文件，汇总风格警察报告
    all_issues = []
    for file_path in state["changed_files"]:
        if not file_path.endswith(".py"): # 过滤非.py文件
            continue

        try:
            result = run(file_path)
        except Exception as e:
            all_issues.append({
                "file": file_path,
                "line": 0,
                "col": 0,
                "rule_id": "ERROR",
                "desc": f"风格警察运行失败: {e}"
            })
            continue
        
        all_issues.extend(result["issues"])

    if _missing:
        try:
            from cr_mas.llm.client import get_fast_llm
            
            prompt = (
                "将以下 flake8 规则描述翻译成中文，简洁准确。\n\n"
                + "\n".join(_missing)
                + "\n\n输出 JSON 对象: {\"原文\": \"中文翻译\", ...}"
            )
            response = get_fast_llm().invoke(prompt)
            new_translations = parse_llm_json(response)
            STYLE_TRANSLATIONS.update(new_translations)
            _save_translations(new_translations)
            _missing.clear()
        except Exception:
            pass

    return{
        "style_report": {
            "agent": "Style",
            "issues": all_issues,
            "summary": {"total": len(all_issues)},
            "missing_translations": list(_missing)
        }
    }

_load_translations() # 模块被import时自动执行

