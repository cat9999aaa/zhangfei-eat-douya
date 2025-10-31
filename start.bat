@echo off
chcp 65001 >nul
echo ====================================================================
echo 张飞吃豆芽 - AI 文章生成器（开发模式）
echo ====================================================================
echo.
echo 提示：如遇到 socket 错误，请使用 start_stable.bat
echo.

echo [1/3] 检查并安装依赖...
pip install -q -r requirements.txt

echo [2/3] 启动应用（开发模式）...
echo.
start "" http://127.0.0.1:5000

echo [3/3] 运行中...
python app.py

pause