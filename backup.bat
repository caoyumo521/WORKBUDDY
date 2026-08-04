@echo off
REM ============================================================
REM  版本备份脚本（Windows）
REM  用法： backup.bat "本次版本说明"
REM  做的事：
REM    1) git add -A        （projects/ 已被 .gitignore 排除，不会带用户数据）
REM    2) git commit        打一个 backup 提交
REM    3) git tag -a        打带时间戳的版本标签，便于回滚
REM    4) git push          推送主分支 + 标签到 GitHub
REM    5) git archive       生成本地快照 zip（仅源码，不含密钥/依赖/用户数据）
REM  回滚： git checkout backup-YYYYMMDD-HHMMSS
REM ============================================================
cd /d %~dp0

set "MSG=%~1"
if "%MSG%"=="" set "MSG=backup"

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "TS=%%i"
set "TAG=backup-%TS%"

echo [1/5] 暂存代码改动...
git add -A
git commit -m "backup: %MSG% @ %TS%" || echo [INFO] 无代码改动，跳过提交

echo [2/5] 打版本标签 %TAG% ...
git tag -a %TAG% -m "backup: %MSG% @ %TS%"

echo [3/5] 推送主分支...
git push origin main || echo [WARN] 主分支推送失败（可能离线），本地标签仍可用

echo [4/5] 推送标签...
git push origin --tags || echo [WARN] 标签推送失败（可能离线），本地标签仍可用

echo [5/5] 生成本地快照...
if not exist backups mkdir backups
git archive --format=zip -o backups\%TAG%.zip HEAD

echo.
echo [OK] 备份完成
echo      标签      : %TAG%
echo      本地快照  : backups\%TAG%.zip
echo      回滚命令  : git checkout %TAG%
echo.
