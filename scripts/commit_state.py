#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions 内用：把更新后的 data + index.html 提交回当前分支。
用法: python3 scripts/commit_state.py
"""
import os, re, subprocess, sys

def run(cmd, check=True):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        sys.exit(r.returncode)
    return r

# 用 runner 名字做提交身份，避免仓库缺 user.email/user.name 时提交失败
user = os.environ.get("GITHUB_ACTOR", "github-actions")
run(f"git config user.email {user}@users.noreply.github.com")
run(f"git config user.name {user}")

# 无任何变更时静默退出，不产生空提交
run("git status --porcelain -- docs", check=False)
run("git add -A -- docs")
if run("git status --porcelain -- docs", check=False).stdout.strip() == "":
    sys.exit(0)

run('git commit -m "chore: 每小时金价数据刷新"')
run("git push origin HEAD")
print("[ok] committed & pushed")
