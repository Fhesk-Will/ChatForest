@echo off
rem ChatForest Windows 开发模式（需先 conda activate chatforest，并安装好前后端依赖）
rem 后端: http://localhost:9000（0.0.0.0 绑定，局域网也可访问）
rem 前端: http://localhost:5173（Vite 热更新）

cd /d %~dp0

start "ChatForest Backend" cmd /k "cd /d %~dp0backend && uvicorn main:app --host 0.0.0.0 --port 9000"

timeout /t 2 /nobreak > nul

start "ChatForest Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Backend:  http://localhost:9000
echo Frontend: http://localhost:5173
echo.
