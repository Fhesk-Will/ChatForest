# -*- mode: python ; coding: utf-8 -*-
# ChatForest Windows 打包配置（文件夹版 onedir）
# 在 Windows 上构建: python -m PyInstaller ChatForest.spec --noconfirm
# 产物: dist/ChatForest/（整个文件夹分发，双击其中的 ChatForest.exe）

a = Analysis(
    ['backend/run_local.py'],
    pathex=['backend'],
    binaries=[],
    datas=[
        # 前端构建产物打进包内，运行时通过 sys._MEIPASS/frontend_dist 访问
        ('frontend/dist', 'frontend_dist'),
    ],
    hiddenimports=[
        # uvicorn 动态导入的模块，PyInstaller 静态分析发现不了，需显式声明
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.http.httptools_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.wsproto_impl',
        'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'anyio._backends._asyncio',
    ],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pytest',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ChatForest',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # 保留控制台窗口，方便看日志；关闭窗口即退出服务
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='ChatForest',
)
