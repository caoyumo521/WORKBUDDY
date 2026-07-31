#!/usr/bin/env bash
# =============================================
# AI 电商详情页工作台 - Linux/Mac 启动脚本
# =============================================

set -e
cd "$(dirname "$0")"

echo ""
echo "========================================"
echo " AI 电商详情页工作台 - 启动中"
echo "========================================"
echo ""

# 1. 后端
if [ ! -d "backend/.venv" ]; then
  echo "[1/3] 创建后端虚拟环境..."
  python3 -m venv backend/.venv
fi

if [ ! -f "backend/.env" ]; then
  echo "  复制 .env.example 到 .env"
  cp backend/.env.example backend/.env
fi

echo "  安装/更新后端依赖..."
backend/.venv/bin/pip install -q -r backend/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 杀掉残留进程
pkill -f "uvicorn app.main" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
sleep 1

# 启动后端
echo "  启动后端服务 (端口 8088)..."
nohup backend/.venv/bin/python backend/run.py > /tmp/dps-backend.log 2>&1 &
echo $! > /tmp/dps-backend.pid

# 2. 前端
echo "[2/3] 准备前端..."
if [ ! -d "frontend/node_modules" ]; then
  echo "  安装前端依赖..."
  (cd frontend && npm install --registry=https://registry.npmmirror.com)
fi

echo "  启动前端服务 (端口 5173)..."
nohup npx vite --root frontend --host 0.0.0.0 --port 5173 > /tmp/dps-frontend.log 2>&1 &
echo $! > /tmp/dps-frontend.pid

sleep 4

echo "[3/3] 启动完成"
echo "  - 前端: http://127.0.0.1:5173/"
echo "  - 后端: http://127.0.0.1:8088/"
echo "  - API 文档: http://127.0.0.1:8088/docs"
echo ""

# 打开浏览器
if command -v open >/dev/null 2>&1; then
  open "http://127.0.0.1:5173/"
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "http://127.0.0.1:5173/"
fi

echo " 停止服务："
echo "   kill \$(cat /tmp/dps-backend.pid) \$(cat /tmp/dps-frontend.pid)"
