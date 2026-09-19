import sys
from pathlib import Path

# 打包模式（PyInstaller）下数据放在 exe 旁边，便携可写；开发模式下放 backend/data
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
