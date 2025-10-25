"""Flask 应用工厂"""

import os
from flask import Flask
from flask_cors import CORS

from app.config.loader import load_config
from app.services import update_comfyui_runtime


def create_app():
    """创建并配置 Flask 应用"""
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')

    # 启用 CORS
    CORS(app)

    # 确保基础目录存在
    os.makedirs('uploads', exist_ok=True)

    # 加载配置并初始化服务
    config = load_config()
    update_comfyui_runtime(config)

    # 注册 blueprints
    from app.views import pages_bp
    from app.api import config_api_bp, main_api_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(config_api_bp)
    app.register_blueprint(main_api_bp)

    return app
