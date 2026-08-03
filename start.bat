@echo off
REM =============================================
REM AI 电商详情页工作台 - Windows 一键启动脚本
REM =============================================

setlocal enabledelayedexpansion
chcp 65001 >nul

cd /d "%~dp0"

echo.
echo ========================================
echo  AI 电商详情页工作台 - 启动中
echo ========================================
echo.

REM ===== 1. 检查 Python =====
where python >nul 2>&1
if errorlevel 1 (
  echo [错误] 未检测到 Python，请先安装 Python 3.10+
  pause
  exit /b 1
)

REM ===== 2. 启动后端 =====
echo [1/3] 准备后端...

if not exist "backend\.venv\Scripts\python.exe" (
  echo  第一次启动，正在创建虚拟环境...
  cd backend
  python -m venv .venv
  cd ..
)

if not exist "backend\.env" (
  echo  复制 .env.example 到 .env
  copy backend\.env.example backend\.env >nul
)

echo  安装/更新后端依赖...
cd backend
call .venv\Scripts\activate.bat
python -m pip install -q -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple 2>nul
cd ..

REM ===== 清理可能残留的 8091/5173 进程与僵尸 socket =====
echo  清理残留的后端/前端进程...

REM 后端 8091
set RETRY=0
:retry_backend
set /a RETRY+=1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8091"') do taskkill /F /PID %%a >nul 2>&1
powershell -NoProfile -Command "try{(New-Object Net.Sockets.TcpClient).Connect('127.0.0.1',8091);exit 0}catch{exit 1}" >nul 2>&1
if errorlevel 1 goto backend_clean_done
if %RETRY% geq 5 goto backend_clean_done
echo  8091 仍有服务，第 %RETRY% 次重试清理...
timeout /t 1 >nul
goto retry_backend
:backend_clean_done
timeout /t 2 >nul

REM 前端 5173
set RETRY=0
:retry_frontend
set /a RETRY+=1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173"') do taskkill /F /PID %%a >nul 2>&1
powershell -NoProfile -Command "try{(New-Object Net.Sockets.TcpClient).Connect('127.0.0.1',5173);exit 0}catch{exit 1}" >nul 2>&1
if errorlevel 1 goto frontend_clean_done
if %RETRY% geq 5 goto frontend_clean_done
echo  5173 仍有服务，第 %RETRY% 次重试清理...
timeout /t 1 >nul
goto retry_frontend
:frontend_clean_done
timeout /t 2 >nul

REM 启动后端
echo  启动后端服务 (端口 8091)...
start "DPS-Backend" /MIN cmd /c "cd /d %~dp0backend && .venv\Scripts\python.exe run.py"

REM ===== 3. 启动前端 =====
echo [2/3] 准备前端...
if not exist "frontend\node_modules" (
  echo  第一次启动，正在安装前端依赖...
  cd frontend
  call npm install --registry=https://registry.npmmirror.com
  cd ..
)

echo  启动前端服务 (端口 5173)...
start "DPS-Frontend" /MIN cmd /c "cd /d %~dp0frontend && npx vite --host 0.0.0.0 --port 5173"

REM ===== 4. 等待并打开浏览器 =====
echo [3/3] 等待服务就绪...
timeout /t 8 >nul

start "" http://127.0.0.1:5173/

echo.
echo ========================================
echo  启动完成！
echo  - 前端: http://127.0.0.1:5173/
echo  - 后端: http://127.0.0.1:8091/
echo  - API 文档: http://127.0.0.1:8091/docs
echo.
echo  按任意键打开浏览器，或 Ctrl+C 关闭
echo ========================================
pause >nul
