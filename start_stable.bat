@echo off
chcp 65001 > nul

echo ====================================================================
echo 张飞吃豆芽 - AI 文章生成器（稳定版）- 最终修复版
echo ====================================================================
echo.
echo --- 步骤 1: 诊断并强制安装依赖 ---
echo.
echo 正在使用以下 Python 环境:
where python
echo.
echo 即将为上述环境安装所有依赖 (from requirements.txt)...
echo 请耐心等待，此过程可能会持续一两分钟。
echo.

REM 强制运行 pip install 并显示所有输出
python -m pip install -r requirements.txt

REM 检查安装是否成功
if errorlevel 1 (
    echo.
    echo ***************************************************************
    echo ** 错误: 依赖安装失败! **
    echo ** 上方应有详细的错误信息。请检查网络或 Python 配置。**
    echo ***************************************************************
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo --- 依赖安装成功! ---
echo.
echo --- 步骤 2: 启动应用 ---
echo.
start "" http://127.0.0.1:5000

echo --- 步骤 3: 运行中... ---
python app_stable.py

pause
