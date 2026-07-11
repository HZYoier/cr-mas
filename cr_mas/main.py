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
    
    click.echo(f"📋 Code Review 报告")

    # 必须修复
    critical = final.get("critical_fixes", [])
    if critical:
        click.echo(f"\n🔴 必须修复 ({len(critical)} 处):")
        for fix in critical:
            where = f"{fix['file']} : {fix['line']}" if fix.get("line") else fix['file']
            click.echo(f"  {where} [{fix['source']}] {fix['type']} - {fix['desc']}")
    
    # 建议修复
    strong = final.get("strong_suggestions", [])
    if strong:
        click.echo(f"\n🟡 建议修复 ({len(strong)} 处):")
        for sug in strong:
            where = f"{sug['file']} : {sug['line']}" if sug.get("line") else sug['file']
            click.echo(f"  {where} [{sug['source']}] {sug['type']} - {sug['desc']}")

    # 可选优化
    optional = final.get("optional_improvements", [])
    if optional:
        click.echo(f"\n🔵 可选优化 ({len(optional)}) 处")
        for opt in optional:
            where = f"{opt['file']} : {opt['line']}" if opt.get("line") else opt['file']
            click.echo(f"  {where} [{opt['source']}] {opt['type']} - {opt['desc']}")

    # 扩展建议
    ext = final.get("extension_advice", [])
    if ext:
        click.echo(f"\n💡 扩展建议（{len(ext)} 项，仅供参考）")
        for item in ext:
            where = f"{item['file']}" if item.get("file") else ""
            hours = f" [预估{item.get('effort_hours')}h]" if item.get("effort_hours") else ""
            click.echo(
                f"   {where} [{item.get('priority', 'MEDIUM')}] {item['type']} {hours}"
            )
            click.echo(f"    {item['desc']}")

    trace = result.get("react_trace", [])
    if trace:
        click.echo(f"\n🧠 主编推理链：")
        for step in trace:
            click.echo(f"  {step}")

    click.echo(f"\n📊 总计: 🔴 {summary['critical']} | 🟡 {summary['strong']} | 🔵 {summary['optional']} | 💡 {summary['extension']}")

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
