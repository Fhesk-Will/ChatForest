# ChatForest 桌面模式启动器（Windows 打包入口，也可在开发模式直接运行）
# 双击 exe / 运行本脚本 → 启动后端 → 自动打开浏览器
import sys
import threading
import time
import urllib.request
import webbrowser

HOST = "127.0.0.1"
PORT = 9000
URL = f"http://{HOST}:{PORT}"


def _server_ready() -> bool:
    """探测后端健康检查接口"""
    try:
        with urllib.request.urlopen(f"{URL}/api/health", timeout=1):
            return True
    except Exception:
        return False


def _open_browser_when_ready():
    """轮询等待后端就绪后打开浏览器（最多等 15 秒）"""
    for _ in range(150):
        if _server_ready():
            break
        time.sleep(0.1)
    webbrowser.open(URL)


def main():
    # 已有实例在运行：直接打开浏览器，避免重复起服务
    if _server_ready():
        print("ChatForest 已在运行，正在打开浏览器...")
        webbrowser.open(URL)
        return

    threading.Thread(target=_open_browser_when_ready, daemon=True).start()

    import uvicorn
    from main import app

    print(f"ChatForest 启动中... 地址: {URL}（关闭本窗口即退出）")
    try:
        uvicorn.run(app, host=HOST, port=PORT, log_level="info")
    except OSError as e:
        print(f"启动失败：端口 {PORT} 可能被其他程序占用。\n详细信息: {e}")
        input("按回车键退出...")
        sys.exit(1)


if __name__ == "__main__":
    main()
