"""文件操作相关的工具函数"""

import os
import re
from datetime import datetime
from werkzeug.utils import secure_filename
from app.config import ALLOWED_EXTENSIONS


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_safe_filename(original_filename, prefix=''):
    """生成安全的文件名，添加时间戳避免重名"""
    filename = secure_filename(original_filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(filename)
    return f"{prefix}{name}_{timestamp}{ext}" if prefix else f"{name}_{timestamp}{ext}"


def sanitize_title(title, max_length=50):
    """清理文件名中的非法字符

    移除Windows和Unix系统中的非法字符，以及可能导致问题的特殊字符
    """
    # 移除Windows非法字符: \ / : * ? " < > |
    # 同时移除中文引号和其他可能导致问题的字符
    safe_title = re.sub(r'[\\/*?:"<>|""'']', '', title)

    # 移除前后空格
    safe_title = safe_title.strip()

    # 限制长度
    safe_title = safe_title[:max_length]

    # 如果清理后为空，使用默认名称
    if not safe_title:
        safe_title = 'untitled'

    return safe_title


def ensure_directory_exists(directory):
    """确保目录存在，不存在则创建"""
    os.makedirs(directory, exist_ok=True)


def find_available_port(start_port=5000, max_attempts=10):
    """查找可用端口，从start_port开始尝试"""
    import socket
    for port in range(start_port, start_port + max_attempts):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('0.0.0.0', port))
            sock.close()
            return port
        except OSError:
            continue
    return None
