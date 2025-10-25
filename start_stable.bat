@echo off
chcp 65001 >nul
echo ====================================================================
echo 张飞吃豆芽 - AI 文章生成器（稳定版）
echo ====================================================================
echo.

echo [1/3] 检查并安装依赖...
pip install -q waitress 2>nul
if errorlevel 1 (
    echo 正在安装 waitress 服务器...
    pip install waitress
)

echo [2/3] 启动应用（使用稳定的 Waitress 服务器）...
echo.
start "" http://127.0.0.1:5000

echo [3/3] 运行中...
python app_stable.py

pause
