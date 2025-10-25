"""网络请求相关的工具函数"""

import requests
from datetime import datetime
import uuid
import os


def download_image_from_url(url, output_dir, timeout=10):
    """从URL下载图片到指定目录"""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()

    # 验证是否为图片
    content_type = response.headers.get('Content-Type', '')
    if not content_type.startswith('image/'):
        raise ValueError('URL不是有效的图片')

    # 生成文件名
    ext = content_type.split('/')[-1]
    allowed_exts = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
    if ext not in allowed_exts:
        ext = 'jpg'

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'temp_{timestamp}_{uuid.uuid4().hex[:8]}.{ext}'

    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'wb') as f:
        f.write(response.content)

    return filepath
