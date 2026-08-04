#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地定时刷新：抓取 DD373 → 生成看板 → 提交并推送 GitHub Pages。
由 macOS launchd 每小时调用（替代 GitHub Actions 不可靠的 cron 调度）。

用法: python3 scripts/refresh_local.py
"""
import subprocess, sys, os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "docs", "data", "gold_history.json")
INDEX = os.path.join(REPO, "docs", "index.html")
SCRIPTS = os.path.join(REPO, "scripts")


def run(cmd, check=True):
    r = subprocess.run(cmd, shell=True, cwd=REPO, capture_output=True, text=True)
    if check and r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        sys.exit(r.returncode)
    return r


def main():
    # 0) 先同步远端，避免基于陈旧状态提交
    run("git fetch origin", check=False)

    run(f"python3 {os.path.join(SCRIPTS, 'fetch_gold.py')} --out {DATA}")
    run(f"python3 {os.path.join(SCRIPTS, 'generate_html.py')} {DATA} {INDEX}")

    # 无变更则结束（数据与上一小时一致时）
    run("git add -A -- docs")
    if run("git status --porcelain -- docs", check=False).stdout.strip() == "":
        print("[skip] 无数据变更")
        return

    # 提交（用本机 git 身份）
    run("git -c user.name=gold-refresh -c user.email=gold-refresh@local commit -m \"chore: 每小时金价数据刷新\"")
    # 推送前先 rebase，避免远端有新提交（如 Actions 或手动触发）导致失败
    run("git pull --rebase origin main", check=False)
    run("git push origin HEAD")
    print("[ok] committed & pushed")


if __name__ == "__main__":
    main()
