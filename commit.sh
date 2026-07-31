#!/usr/bin/env bash
# 一键提交当前迭代：./commit.sh "feat: 完成 XXX 功能"
msg="${1:-chore: 迭代提交}"
git add -A
git commit -m "$msg"
echo "=== 最新版本 ==="
git log --oneline -1
