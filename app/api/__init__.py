"""API路由模块"""

from .config_api import config_api_bp
from .main_api import main_api_bp

__all__ = ['config_api_bp', 'main_api_bp']
