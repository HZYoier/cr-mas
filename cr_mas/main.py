"""CR-MAS CLI 入口"""

import click
from cr_mas.graph.builder import build_review_graph
from cr_mas.tools.git_parser import parse_staged_diff
from cr_mas.memory.sqlite_store import save_review
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()

# flake8 规则翻译映射表
FLAKE8_RULES = {
    "E": "格式问题",
    "W": "格式建议",
    "F": "未使用变量/import",
    "N": "命名规范",
    "B": "常见陷阱",
    "D": "文档注释",
    "C": "圈复杂度"
}

@click.group()
def cli():
    pass

@cli.command()
@click.option("-m", "--message", required = True, help = "Commit message")
@click.option("--no-fail", is_flag = True, help = "审查不通过也允许提交")
@click.option("--skip_review", is_flag = True, help = "跳过审查直接提交")
def commit(message, no_fail, skip_review):
    # 提交前触发多智能体审查
    click.echo(f"🔍 审查启动: {message}")

    if skip_review:
        click.echo("⏭️  跳过审查，直接提交")
        subprocess.run(["git", "commit", "-m", message], check=True)
        return

    try:
        git_data = parse_staged_diff(".")
    except RuntimeError as e:
        click.echo(f"❌ 错误：{e}")
        return
    
    if not git_data["changed_files"]:
        click.echo("⚠️  暂存区没有变更，无需审查。")
        return
    
    graph = build_review_graph()
    with console.status("[bold green]🔍 审查中...[/bold green]", spinner = "dots12"):
        result = graph.invoke({
        "changed_files": git_data["changed_files"],
        "raw_diff": git_data["raw_diff"],
        "commit_hash": git_data["commit_hash"]
    })
    final = result.get("final_report")
    summary = final.get("summary", {})
    save_review(result)

    if not final:
        click.echo("❌ 主编未生成报告")
        return
    
    console.print(Panel.fit("[bold]Code Review Report[/bold]", border_style="cyan"))


    # 必须修复
    critical = final.get("critical_fixes", [])
    if critical:
        table = Table(title="🔴 必须修复", box=box.SIMPLE, title_style="bold red", row_styles=["", "dim"])
        table.add_column("位置", style="dim")
        table.add_column("来源")
        table.add_column("描述")
        for fix in critical:
            where = f"{fix.get('file', '')}:{fix.get('line', '')}" if fix.get("line") else fix.get("file")
            desc = f"[{fix.get('type', '')}] {fix.get('desc', '')}"
            table.add_row(where, fix.get("source", ""), desc)
        console.print(table)

    
    # 建议修复
    strong = final.get("strong_suggestions", [])
    if strong:
        table = Table(title="🟡 强烈建议", box=box.SIMPLE, title_style="bold yellow", row_styles=["", "dim"])
        table.add_column("位置", style="dim")
        table.add_column("来源")
        table.add_column("描述")
        for sug in strong:
            where = f"{sug.get('file', '')}:{sug.get('line', '')}" if sug.get("line") else sug.get("file")
            table.add_row(where, sug.get("source", ""), sug.get("desc", ""))
        console.print(table)


    # 可选优化
        optional = final.get("optional_improvements", [])
    if optional:
        table = Table(title="🔵 可选优化", box=box.SIMPLE, title_style="bold blue", row_styles=["", "dim"])
        table.add_column("位置", style="dim")
        table.add_column("来源")
        table.add_column("描述")
        for opt in optional:
            where = f"{opt.get('file', '')}:{opt.get('line', '')}" if opt.get("line") else opt.get("file")
            rule_prefix = opt.get("type", "").split(" - ")[-1][0] if " - " in opt.get("type", "") else ""
            category = FLAKE8_RULES.get(rule_prefix, "风格")
            table.add_row(where, category, opt.get("desc", ""))
        console.print(table)


    # 扩展建议
    ext = final.get("extension_advice", [])
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    ext = sorted(ext, key=lambda x: priority_order.get(x.get("priority", "LOW"), 99))

    if ext:
        table = Table(title="💡 扩展建议（仅供参考）", box=box.SIMPLE, title_style="bold green", row_styles=["", "dim"])
        table.add_column("位置", style="dim")
        table.add_column("优先级")
        table.add_column("类型")
        table.add_column("描述", overflow = None)
        for item in ext:
            where = item.get("file", "")
            line = item.get("line")
            if line:
                where += f":{line}"
            desc = item.get("desc", "")
            table.add_row(
                where,
                item.get("priority", ""),
                item.get("type", ""),
                desc,
            )
        console.print(table)

    # 主编推理链
    trace = result.get("react_trace", [])
    if trace:
        console.print(Panel(
            "\n".join(trace),
            title="🧠 主编推理链",
            border_style="dim",
        ))

    # 汇总
    console.print(Panel.fit(
        f"🔴 {summary.get('critical', 0)} | 🟡 {summary.get('strong', 0)} | 🔵 {summary.get('optional', 0)} | 💡 {summary.get('extension', 0)}",
        title="📊 总计",
        border_style="cyan",
    ))


    # 是否允许提交，有严重问题时阻止提交
    critical_count = summary.get("critical", 0)
    if critical_count > 0 and not no_fail:
        click.echo(
            f"\n🔴 发现 {critical_count} 个严重问题，提交已阻止。"
            f"\n   请修复标记为 🔴 必须修复 的项目。"
        )
        return

    subprocess.run(["git", "commit", "-m", message], check = True)
    click.echo(f"\n✅ 提交成功，审查报告已存档。")

@cli.command()
@click.option("--limit", default = 10, help = "显示条数")
def history(limit):
    # 查看历史审查记录
    from cr_mas.memory.sqlite_store import get_review_history
    
    rows = get_review_history(limit)
    if not rows:
        click.echo("📭 暂无审查记录")
        return
    
    click.echo(f"\n📋 最近 {len(rows)} 次审查记录\n")
    for r in rows:
        click.echo(
            f"  [{r['created_at']}]"
            f"🔴 {r['critical_count']} 严重 | 🟡 {r['total_issues']} 问题"
        )

if __name__ == "__main__":
    cli()
