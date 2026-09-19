#!/bin/bash
set -e

# 初始化 conda（非交互式 shell 需要这一步）
eval "$(conda shell.bash hook)"
conda activate chatforest

cd "$(dirname "$0")"

echo ">>> Python: $(which python) ($(python --version 2>&1))"
echo ""

echo ">>> 构建前端..."
cd frontend
npm install
npm run build
cd ..

echo ">>> 启动后端服务..."
IP=$(hostname -I | awk '{print $1}')
echo ">>> 本机访问: http://localhost:9000"
echo ">>> 局域网访问: http://${IP}:9000"
cd backend
uvicorn main:app --host 0.0.0.0 --port 9000
