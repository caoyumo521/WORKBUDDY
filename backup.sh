#!/usr/bin/env bash
# ============================================================
#  版本备份脚本（macOS / Linux）
#  用法： bash backup.sh "本次版本说明"
#  做的事：
#    1) git add -A        （projects/ 已被 .gitignore 排除，不会带用户数据）
#    2) git commit        打一个 backup 提交
#    3) git tag -a        打带时间戳的版本标签，便于回滚
#    4) git push          推送主分支 + 标签到 GitHub
#    5) git archive       生成本地快照 zip（仅源码，不含密钥/依赖/用户数据）
#  回滚： git checkout backup-YYYYMMDD-HHMMSS
# ============================================================
set -u
cd "$(dirname "$0")"

MSG="${1:-backup}"
TS=$(date +%Y%m%d-%H%M%S)
TAG="backup-$TS"

echo "[1/5] 暂存代码改动..."
git add -A
git commit -m "backup: $MSG @ $TS" || echo "[INFO] 无代码改动，跳过提交"

echo "[2/5] 打版本标签 $TAG ..."
git tag -a "$TAG" -m "backup: $MSG @ $TS"

echo "[3/5] 推送主分支..."
git push origin main || echo "[WARN] 主分支推送失败（可能离线），本地标签仍可用"

echo "[4/5] 推送标签..."
git push origin --tags || echo "[WARN] 标签推送失败（可能离线），本地标签仍可用"

echo "[5/5] 生成本地快照..."
mkdir -p backups
git archive --format=zip -o "backups/$TAG.zip" HEAD

echo
echo "[OK] 备份完成"
echo "      标签      : $TAG"
echo "      本地快照  : backups/$TAG.zip"
echo "      回滚命令  : git checkout $TAG"
echo
