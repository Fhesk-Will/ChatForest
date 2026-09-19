#!/usr/bin/env python3
# 一次性验证脚本: 停后台服务 → 测试 backend/run_local.py → 恢复后台服务
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PID_FILE = ROOT / "logs" / "backend.pid"
# 抑制测试过程中的浏览器弹窗
TEST_ENV = {**os.environ, "BROWSER": "/bin/true"}


def _find_env_python() -> str:
    """定位 chatforest 环境的 python（uvicorn/fastapi 装在该环境里）"""
    exe = Path(sys.executable).resolve()
    if "envs/chatforest" in str(exe):
        return str(exe)
    import shutil

    conda = shutil.which("conda")
    candidates = []
    if conda:
        base = subprocess.run([conda, "info", "--base"], capture_output=True, text=True)
        if base.returncode == 0:
            candidates.append(Path(base.stdout.strip()) / "envs/chatforest/bin/python")
    for home_name in ("miniconda3", "anaconda3", "miniforge3"):
        candidates.append(Path.home() / home_name / "envs/chatforest/bin/python")
    for c in candidates:
        if c.exists():
            return str(c)
    raise SystemExit("找不到 chatforest 环境的 python")


# 确保在 chatforest 环境的 python 下运行（run_local 依赖环境里的 uvicorn）
if "envs/chatforest" not in str(Path(sys.executable).resolve()):
    os.execv(_find_env_python(), [_find_env_python(), __file__])


def health_ok() -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:9000/api/health", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def stop_service():
    if PID_FILE.exists():
        pid = int(PID_FILE.read_text().strip())
        try:
            os.kill(pid, 15)
            for _ in range(20):
                try:
                    os.kill(pid, 0)
                    time.sleep(0.5)
                except ProcessLookupError:
                    break
            print(f"[1] 后台服务已停止 (原 PID {pid})")
        except ProcessLookupError:
            print(f"[1] PID {pid} 已不存在")
        PID_FILE.unlink(missing_ok=True)
    else:
        print("[1] 无 PID 文件，跳过停止")


stop_service()

# [2] 启动 run_local.py（开发模式），等待健康检查通过
proc = subprocess.Popen(
    [sys.executable, str(ROOT / "backend" / "run_local.py")],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=TEST_ENV,
)
ok = False
for _ in range(100):
    if health_ok():
        ok = True
        break
    time.sleep(0.2)
print(f"[2] run_local.py 启动后端: {'成功' if ok else '失败'}")

# [3] 首页可访问
try:
    with urllib.request.urlopen("http://127.0.0.1:9000/", timeout=3) as r:
        print(f"[3] 首页 HTTP {r.status}, 内容 {len(r.read())} 字节")
except Exception as e:
    print(f"[3] 首页访问失败: {e}")

# [4] 防重复启动：再次运行 run_local.py 应提示已在运行并直接退出
try:
    r2 = subprocess.run(
        [sys.executable, str(ROOT / "backend" / "run_local.py")],
        capture_output=True, text=True, timeout=30, env=TEST_ENV,
    )
    out = (r2.stdout + r2.stderr).strip()
    print(f"[4] 二次启动输出: {out!r}")
    print(f"[4] 防重复启动: {'通过' if '已在运行' in out else '未确认'}")
except subprocess.TimeoutExpired:
    print("[4] 二次启动超时（异常，应立即返回）")

# [5] 停掉测试进程
proc.terminate()
try:
    proc.wait(timeout=10)
except subprocess.TimeoutExpired:
    proc.kill()
print("[5] 测试进程已停止")

# [6] 恢复后台服务
subprocess.run(["bash", "service.sh", "start"], cwd=ROOT, check=True)
print("[6] 后台服务已恢复")
