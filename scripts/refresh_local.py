#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地定时刷新：抓取 DD373 → 生成看板 → 提交并推送 GitHub Pages。
由 macOS launchd 错峰调用，作为外部定时器的陈旧数据兜底。

用法: python3 scripts/refresh_local.py [--fallback]
"""
import subprocess, sys, os, json
from datetime import datetime, timedelta, timezone

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "docs", "data", "gold_history.json")
INDEX = os.path.join(REPO, "docs", "index.html")
SCRIPTS = os.path.join(REPO, "scripts")
FALLBACK_STALE_MINUTES = 75


def run(cmd, check=True):
    r = subprocess.run(cmd, shell=True, cwd=REPO, capture_output=True, text=True)
    if check and r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        sys.exit(r.returncode)
    return r


def remote_latest_age_minutes():
    """读取 origin/main 的最后有效快照年龄；解析失败时拒绝盲目覆盖。"""
    result = run("git show origin/main:docs/data/gold_history.json")
    data = json.loads(result.stdout)
    history = data.get("history")
    if not isinstance(history, list) or not history:
        raise RuntimeError("远端历史为空，拒绝执行兜底写入")
    latest = history[-1].get("time")
    if not isinstance(latest, str):
        raise RuntimeError("远端最新时间无效，拒绝执行兜底写入")
    timestamp = datetime.strptime(latest, "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=timezone(timedelta(hours=8))
    )
    now = datetime.now(timezone(timedelta(hours=8)))
    return (now - timestamp).total_seconds() / 60


def main():
    fallback = "--fallback" in sys.argv

    # 0) 严格同步远端，避免基于陈旧状态提交或覆盖云端更新
    run("git fetch origin")
    run("git pull --ff-only origin main")

    if fallback:
        age = remote_latest_age_minutes()
        if age < FALLBACK_STALE_MINUTES:
            print(f"[skip] 远端数据仅 {age:.1f} 分钟，外部刷新正常")
            return
        print(f"[fallback] 远端数据已陈旧 {age:.1f} 分钟，启动本机兜底")

    run(f"python3 {os.path.join(SCRIPTS, 'fetch_gold.py')} --out {DATA}")
    run(f"python3 {os.path.join(SCRIPTS, 'generate_html.py')} {DATA} {INDEX}")

    # 无变更则结束（数据与上一小时一致时）
    run("git add -A -- docs")
    if run("git status --porcelain -- docs", check=False).stdout.strip() == "":
        print("[skip] 无数据变更")
        return

    # 提交（用本机 git 身份）
    run("git -c user.name=gold-refresh -c user.email=gold-refresh@local commit -m \"chore: 每小时金价数据刷新\"")
    run("git push origin HEAD")
    print("[ok] committed & pushed")


if __name__ == "__main__":
    main()
