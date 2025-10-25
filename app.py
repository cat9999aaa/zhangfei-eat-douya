"""
张飞吃豆芽 - AI 文章生成器
重构后的入口文件
"""

import os
from app import create_app
from app.utils.file_helpers import find_available_port

if __name__ == '__main__':
    # 只在主进程中查找端口（避免debug模式重载器重复查找）
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # 这是主进程，查找可用端口
        port = find_available_port(5000)
        if port is None:
            print("错误: 无法找到可用端口 (5000-5009 都被占用)")
            exit(1)

        if port != 5000:
            print(f"提示: 端口 5000 被占用，使用端口 {port} 启动服务")

        print(f"应用启动在 http://localhost:{port}")
        # 将端口保存到环境变量，供重载器进程使用
        os.environ['APP_PORT'] = str(port)
    else:
        # 这是重载器进程，使用已找到的端口
        port = int(os.environ.get('APP_PORT', 5000))

    # 创建应用实例
    app = create_app()

    # 启动应用
    # 在Windows上禁用threaded模式以避免套接字错误
    app.run(debug=True, host='0.0.0.0', port=port, threaded=False)
