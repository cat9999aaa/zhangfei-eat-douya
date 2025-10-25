"""
张飞吃豆芽 - AI 文章生成器
稳定版启动脚本（使用 waitress 服务器）

使用方法：
    python app_stable.py

注意：
    首次使用需要安装 waitress：
    pip install waitress
"""

import os
import sys
import logging
from app import create_app
from app.utils.file_helpers import find_available_port

# 配置 Waitress 日志级别，减少警告信息
logging.getLogger('waitress').setLevel(logging.ERROR)

def main():
    """使用 waitress 服务器启动应用（生产级，稳定）"""
    try:
        # 尝试导入 waitress
        from waitress import serve
    except ImportError:
        print("=" * 60)
        print("错误: 未安装 waitress 服务器")
        print("=" * 60)
        print("\n请先安装 waitress：")
        print("  pip install waitress")
        print("\n或者使用开发模式启动：")
        print("  python app.py")
        print("=" * 60)
        sys.exit(1)

    # 查找可用端口
    port = find_available_port(5000)
    if port is None:
        print("错误: 无法找到可用端口 (5000-5009 都被占用)")
        sys.exit(1)

    if port != 5000:
        print(f"提示: 端口 5000 被占用，使用端口 {port} 启动服务")

    # 创建应用实例
    app = create_app()

    print("\n" + "=" * 60)
    print("🚀 张飞吃豆芽 - AI 文章生成器 (稳定版)")
    print("=" * 60)
    print(f"✓ 服务器地址: http://localhost:{port}")
    print(f"✓ 使用 Waitress 服务器（推荐用于长时间运行）")
    print(f"✓ 工作线程: 8 个")
    print(f"✓ 请求超时: 180 秒")
    print("✓ 按 Ctrl+C 停止服务")
    print("=" * 60 + "\n")

    # 使用 waitress 服务器启动
    serve(
        app,
        host='0.0.0.0',
        port=port,
        threads=8,  # 8 个线程足够处理并发请求（包括慢速 API 调用）
        url_scheme='http',
        channel_timeout=180,  # 通道超时 180 秒（适合 Gemini 等 API 调用）
        asyncore_loop_timeout=1,
        send_bytes=8192,
        recv_bytes=8192,
        connection_limit=100,  # 最大连接数
        cleanup_interval=30,  # 每 30 秒清理一次过期连接
        log_socket_errors=False,  # 不记录 socket 错误（减少日志噪音）
    )

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n正在停止服务器...")
        print("服务器已停止。")
    except Exception as e:
        print(f"\n启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
