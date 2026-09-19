@echo off
rem ChatForest Windows 一键打包脚本（需在 chatforest conda 环境中执行）
rem 用法: conda activate chatforest && build_exe.bat
rem 产物: dist\ChatForest\ChatForest.exe（整个 ChatForest 文件夹即可分发）

cd /d %~dp0

python -m pip install -r backend/requirements.txt pyinstaller || goto :err

echo.
echo [1/2] 构建前端...
cd frontend
call npm install || goto :err
call npm run build || goto :err
cd ..

echo.
echo [2/2] PyInstaller 打包...
python -m PyInstaller ChatForest.spec --noconfirm || goto :err

echo.
echo ============================================
echo 打包完成: dist\ChatForest\ChatForest.exe
echo 分发时请拷贝整个 ChatForest 文件夹
echo ============================================
pause
exit /b 0

:err
echo.
echo 构建失败，请检查上方错误信息
pause
exit /b 1
