# -*- coding: utf-8 -*-
"""运营日报快照：运行 stats.py 并把结果存档为 docs/运营日报/YYYY-MM-DD.md"""
import datetime
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_DIR = os.path.join(PROJECT_ROOT, "docs", "运营日报")


def main():
    out = subprocess.run(
        [sys.executable, os.path.join(PROJECT_ROOT, "app", "stats.py")],
        capture_output=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    report = out.stdout if out.returncode == 0 else (out.stdout + out.stderr)

    os.makedirs(REPORT_DIR, exist_ok=True)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(REPORT_DIR, f"{today}.md")
    content = (
        f"# 运营日报 {today}\n\n"
        "> 自动生成快照（每日 8:47 定时 / 可手动运行 python app/daily_report.py 刷新当天快照）\n"
        "> 深度分析见当天工作日志与人工整理版\n\n"
        "```\n" + report + "```\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"运营日报快照已生成：{path}")


if __name__ == "__main__":
    main()
