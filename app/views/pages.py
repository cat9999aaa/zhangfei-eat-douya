"""页面视图路由"""

from flask import Blueprint, render_template

pages_bp = Blueprint('pages', __name__)


@pages_bp.route('/')
def index():
    """渲染写作页面"""
    return render_template('write.html')


@pages_bp.route('/config')
def config_page():
    """渲染配置页面"""
    return render_template('config.html')


@pages_bp.route('/history')
def history_page():
    """渲染历史记录页面"""
    return render_template('history.html')
