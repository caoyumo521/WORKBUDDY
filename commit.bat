@echo off
REM 一键提交当前迭代：commit.bat "feat: 完成 XXX 功能"
set msg=%~1
if "%msg%"=="" set msg=chore: 迭代提交
git add -A
git commit -m "%msg%"
echo === 最新版本 ===
git log --oneline -1
