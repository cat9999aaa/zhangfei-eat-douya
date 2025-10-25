"""图片处理和下载服务模块"""

import os
import random
import requests
from datetime import datetime
import uuid
from app.config import ALLOWED_EXTENSIONS
from app.config.loader import load_config


def _download_and_save_image(image_url):
    """从 URL 下载图片并保存为临时文件"""
    try:
        image_response = requests.get(image_url, timeout=15)
        image_response.raise_for_status()

        config = load_config()
        # 将临时图片保存到 uploads 目录，便于管理
        output_dir = config.get('uploaded_images_dir', 'uploads')
        os.makedirs(output_dir, exist_ok=True)

        image_path = os.path.join(output_dir, f'temp_{uuid.uuid4().hex}.jpg')
        with open(image_path, 'wb') as f:
            f.write(image_response.content)

        return image_path
    except Exception as e:
        print(f"下载图片失败 ({image_url[:40]}...): {e}")
        return None


def fetch_unsplash_image_urls(keyword, access_key):
    """从 Unsplash 获取图片 URL 列表"""
    try:
        search_url = 'https://api.unsplash.com/search/photos'
        headers = {'Authorization': f'Client-ID {access_key}'}
        params = {'query': keyword, 'per_page': 20, 'orientation': 'landscape'}

        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        if not data.get('results'):
            return []

        return [img['urls']['regular'] for img in data['results']]
    except Exception as e:
        print(f"Unsplash 获取 URL 失败: {e}")
        return []


def fetch_pexels_image_urls(keyword, api_key):
    """从 Pexels 获取图片 URL 列表"""
    try:
        search_url = 'https://api.pexels.com/v1/search'
        headers = {'Authorization': api_key}
        params = {'query': keyword, 'per_page': 20, 'orientation': 'landscape'}

        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        if not data.get('photos'):
            return []

        return [photo['src']['large'] for photo in data['photos']]
    except Exception as e:
        print(f"Pexels 获取 URL 失败: {e}")
        return []


def fetch_pixabay_image_urls(keyword, api_key):
    """从 Pixabay 获取图片 URL 列表"""
    try:
        search_url = 'https://pixabay.com/api/'
        params = {
            'key': api_key,
            'q': keyword,
            'per_page': 20,
            'image_type': 'photo',
            'orientation': 'horizontal'
        }

        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        if not data.get('hits'):
            return []

        return [hit['largeImageURL'] for hit in data['hits']]
    except Exception as e:
        print(f"Pixabay 获取 URL 失败: {e}")
        return []


def get_local_image_paths(tags=None, config=None):
    """从本地图库中根据标签获取图片路径列表"""
    try:
        if not config:
            config = load_config()

        local_dirs = config.get('local_image_directories', [{'path': 'pic', 'tags': ['default']}])

        if tags:
            matching_dirs = [d for d in local_dirs if any(tag in d.get('tags', []) for tag in tags)]
            if matching_dirs:
                local_dirs = matching_dirs

        available_images = []
        for dir_config in local_dirs:
            dir_path = dir_config.get('path', '')
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                for file in os.listdir(dir_path):
                    file_path = os.path.join(dir_path, file)
                    if os.path.isfile(file_path) and file.lower().endswith(tuple(ALLOWED_EXTENSIONS)):
                        available_images.append(file_path)

        return available_images

    except Exception as e:
        print(f"从本地图库获取图片失败: {e}")
        return []


def list_local_images(config):
    """列出本地图库中的所有图片"""
    local_dirs = config.get('local_image_directories', [{'path': 'pic', 'tags': ['default']}])

    images = []
    for dir_config in local_dirs:
        dir_path = dir_config.get('path', '')
        dir_tags = dir_config.get('tags', [])

        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            for file in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file)
                if os.path.isfile(file_path) and file.lower().endswith(tuple(ALLOWED_EXTENSIONS)):
                    images.append({
                        'filename': file,
                        'path': file_path,
                        'directory': dir_path,
                        'tags': dir_tags
                    })

    return images


def list_uploaded_images(config):
    """列出用户上传的所有图片"""
    upload_dir = config.get('uploaded_images_dir', 'uploads')

    images = []
    if os.path.exists(upload_dir) and os.path.isdir(upload_dir):
        for file in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, file)
            # 过滤掉临时文件
            if os.path.isfile(file_path) and file.lower().endswith(tuple(ALLOWED_EXTENSIONS)) and not file.startswith('temp_'):
                stat = os.stat(file_path)
                images.append({
                    'filename': file,
                    'path': file_path,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                })

    images.sort(key=lambda x: x['created'], reverse=True)
    return images


def test_unsplash_connection(access_key):
    """测试 Unsplash API 配置"""
    try:
        search_url = 'https://api.unsplash.com/search/photos'
        headers = {'Authorization': f'Client-ID {access_key}'}
        params = {'query': 'nature', 'per_page': 1}

        response = requests.get(search_url, headers=headers, params=params, timeout=10)

        if response.status_code == 401:
            return False, 'Access Key 无效或已过期', None
        elif response.status_code == 403:
            return False, '请求频率超限，请稍后再试', None

        response.raise_for_status()
        data = response.json()

        if data.get('results') and len(data['results']) > 0:
            image_url = data['results'][0]['urls']['small']
            return True, 'Unsplash API 工作正常', image_url
        else:
            return False, '未找到测试图片', None

    except requests.exceptions.Timeout:
        return False, '请求超时，可能是网络问题', None
    except requests.exceptions.ConnectionError:
        return False, '无法连接到 Unsplash API，请检查网络', None
    except Exception as e:
        return False, f'测试失败: {str(e)}', None


def test_pexels_connection(api_key):
    """测试 Pexels API 配置"""
    try:
        search_url = 'https://api.pexels.com/v1/search'
        headers = {'Authorization': api_key}
        params = {'query': 'nature', 'per_page': 1}

        response = requests.get(search_url, headers=headers, params=params, timeout=10)

        if response.status_code == 401:
            return False, 'API Key 无效或已过期', None
        elif response.status_code == 403:
            return False, '请求频率超限，请稍后再试', None

        response.raise_for_status()
        data = response.json()

        if data.get('photos') and len(data['photos']) > 0:
            image_url = data['photos'][0]['src']['small']
            return True, 'Pexels API 工作正常', image_url
        else:
            return False, '未找到测试图片', None

    except requests.exceptions.Timeout:
        return False, '请求超时，可能是网络问题', None
    except requests.exceptions.ConnectionError:
        return False, '无法连接到 Pexels API，请检查网络', None
    except Exception as e:
        return False, f'测试失败: {str(e)}', None


def test_pixabay_connection(api_key):
    """测试 Pixabay API 配置"""
    try:
        search_url = 'https://pixabay.com/api/'
        params = {'key': api_key, 'q': 'nature', 'per_page': 3}

        response = requests.get(search_url, params=params, timeout=10)

        if response.status_code == 401 or response.status_code == 400:
            return False, 'API Key 无效或已过期', None

        response.raise_for_status()
        data = response.json()

        if data.get('hits') and len(data['hits']) > 0:
            image_url = data['hits'][0]['webformatURL']
            return True, 'Pixabay API 工作正常', image_url
        else:
            return False, '未找到测试图片', None

    except requests.exceptions.Timeout:
        return False, '请求超时，可能是网络问题', None
    except requests.exceptions.ConnectionError:
        return False, '无法连接到 Pixabay API，请检查网络', None
    except Exception as e:
        return False, f'测试失败: {str(e)}', None
