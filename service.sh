#!/bin/bash
# ChatForest 后台服务管理脚本
# 用法: bash service.sh {start|stop|restart|status|logs}
set -e

cd "$(dirname "$0")"

PORT=9000
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/backend.log"
PID_FILE="$LOG_DIR/backend.pid"

# 检查进程是否存活（PID 文件存在且进程在跑）
is_running() {
    [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

# 打印访问地址
print_urls() {
    local IP
    IP=$(hostname -I | awk '{print $1}')
    echo ">>> 本机访问:   http://localhost:$PORT"
    echo ">>> 局域网访问: http://$IP:$PORT"
}

# 等待服务就绪（最多 10 秒）
wait_ready() {
    for _ in $(seq 1 20); do
        if curl -s -o /dev/null --max-time 1 "http://localhost:$PORT/api/health"; then
            return 0
        fi
        sleep 0.5
    done
    return 1
}

start() {
    if is_running; then
        echo ">>> 服务已在运行 (PID $(cat "$PID_FILE"))"
        print_urls
        exit 0
    fi

    mkdir -p "$LOG_DIR"

    # dist 缺失时才构建前端，避免每次启动都 npm install
    if [ ! -f frontend/dist/index.html ]; then
        echo ">>> 首次运行，构建前端..."
        cd frontend
        npm install
        npm run build
        cd ..
    fi

    # 初始化 conda（非交互式 shell 需要这一步）
    eval "$(conda shell.bash hook)"
    conda activate chatforest

    echo ">>> 后台启动服务..."
    cd backend
    nohup uvicorn main:app --host 0.0.0.0 --port "$PORT" >> "../$LOG_FILE" 2>&1 < /dev/null &
    echo $! > "../$PID_FILE"
    cd ..

    if wait_ready; then
        echo ">>> 服务已启动 (PID $(cat "$PID_FILE"))，日志: $LOG_FILE"
        print_urls
    else
        echo ">>> 启动失败，查看日志: tail -50 $LOG_FILE"
        exit 1
    fi
}

stop() {
    if ! is_running; then
        echo ">>> 服务未在运行"
        rm -f "$PID_FILE"
        exit 0
    fi

    local PID
    PID=$(cat "$PID_FILE")
    echo ">>> 停止服务 (PID $PID)..."
    kill "$PID" 2>/dev/null || true

    # 最多等 5 秒优雅退出，之后强制 kill
    for _ in $(seq 1 10); do
        kill -0 "$PID" 2>/dev/null || break
        sleep 0.5
    done
    if kill -0 "$PID" 2>/dev/null; then
        echo ">>> 进程未响应，强制结束"
        kill -9 "$PID" 2>/dev/null || true
    fi

    rm -f "$PID_FILE"
    echo ">>> 服务已停止"
}

status() {
    if is_running; then
        echo ">>> 服务运行中 (PID $(cat "$PID_FILE"))"
        if curl -s --max-time 2 "http://localhost:$PORT/api/health"; then
            echo ""
        fi
        print_urls
    else
        echo ">>> 服务未在运行"
        exit 1
    fi
}

case "${1:-}" in
    start)   start ;;
    stop)    stop ;;
    restart) stop; start ;;
    status)  status ;;
    logs)    tail -f "$LOG_FILE" ;;
    *)
        echo "用法: bash service.sh {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
