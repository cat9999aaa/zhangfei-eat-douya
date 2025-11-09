"""网络请求相关的工具函数"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import uuid
import os

from urllib.parse import urlparse

def fetch_real_url_and_title(redirect_url, timeout=10):
    """
    获取重定向链接的真实 URL、页面标题、网站名称和语言。
    优先从站点主页获取网站名称，以获得最高准确性。
    """
    try:
        # --- 步骤 1: 获取文章页信息 ---
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }
        article_response = requests.get(redirect_url, headers=headers, timeout=timeout, allow_redirects=True)
        article_response.raise_for_status()

        real_url = article_response.url
        article_soup = BeautifulSoup(article_response.content, 'html.parser')

        # 初始化返回值
        article_title = ''
        site_name = ''
        lang = 'unknown'

        # 从文章页获取语言和默认标题
        if article_soup.html and article_soup.html.get('lang'):
            lang = article_soup.html.get('lang').lower()
        if article_soup.title and article_soup.title.string:
            article_title = article_soup.title.string.strip()

        # --- 步骤 2: 从主页获取网站名称 (用户建议的绝佳方案) ---
        try:
            parsed_url = urlparse(real_url)
            homepage_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            homepage_response = requests.get(homepage_url, headers=headers, timeout=5) # 较短的超时
            if homepage_response.ok:
                homepage_soup = BeautifulSoup(homepage_response.content, 'html.parser')
                if homepage_soup.title and homepage_soup.title.string:
                    site_name = homepage_soup.title.string.strip()
                    # 清理主页标题，可能包含 "首页" 等词
                    for keyword in ['首页', '官网', 'Official Website', '官方网站']:
                        site_name = site_name.replace(keyword, '').strip(' -|_—')
        except Exception as e:
            print(f"  ...获取主页标题失败 ({e})，将回退到备选方案")

        # --- 步骤 3: 备选方案 (如果主页获取失败) ---
        if not site_name:
            # 尝试从文章页标题推断
            for separator in [' - ', ' | ', '_', '—', '-', '|']:
                if separator in article_title:
                    parts = article_title.rsplit(separator, 1)
                    if len(parts) > 1 and 0 < len(parts[1]) < 30:
                        site_name = parts[1].strip()
                        article_title = parts[0].strip() # 更新文章标题
                        break

        # --- 步骤 4: 最终备选 (如果全部失败) ---
        if not site_name:
            parsed_url = urlparse(real_url)
            site_name = parsed_url.netloc.replace('www.', '')

        # --- 步骤 5: 最终清洗文章标题 ---
        # 确保文章标题不包含网站名
        if site_name and site_name in article_title:
            article_title = article_title.replace(site_name, '').strip(' -|_—')
        # 再次清洗
        for separator in [' - ', ' | ', '_', '—', '-', '|']:
            if separator in article_title:
                article_title = article_title.split(separator)[0].strip()

        return real_url, article_title, site_name, lang

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {redirect_url}: {e}")
        return redirect_url, '', '', 'unknown'



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
