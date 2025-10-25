"""图片处理和下载服务模块"""

import os
import random
import requests
from datetime import datetime
import uuid
from app.config import ALLOWED_EXTENSIONS
from app.config.loader import load_config


def download_unsplash_image(keyword, access_key):
    """从 Unsplash 下载图片"""
    try:
        search_url = 'https://api.unsplash.com/search/photos'
        headers = {'Authorization': f'Client-ID {access_key}'}
        params = {'query': keyword, 'per_page': 1, 'orientation': 'landscape'}

        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        if not data['results']:
            return None

        image_url = data['results'][0]['urls']['regular']
        image_response = requests.get(image_url, timeout=10)
        image_response.raise_for_status()

        config = load_config()
        output_dir = config.get('output_directory', 'output')
        os.makedirs(output_dir, exist_ok=True)
        image_path = os.path.join(output_dir, f'temp_{datetime.now().strftime("%Y%m%d%H%M%S")}_{uuid.uuid4().hex[:8]}.jpg')
        with open(image_path, 'wb') as f:
            f.write(image_response.content)

        return image_path

    except Exception as e:
        print(f"Unsplash 下载图片失败: {e}")
        return None


def download_pexels_image(keyword, api_key):
    """从 Pexels 下载图片"""
    try:
        search_url = 'https://api.pexels.com/v1/search'
        headers = {'Authorization': api_key}
        params = {'query': keyword, 'per_page': 1, 'orientation': 'landscape'}

        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        if not data.get('photos'):
            return None

        image_url = data['photos'][0]['src']['large']
        image_response = requests.get(image_url, timeout=10)
        image_response.raise_for_status()

        config = load_config()
        output_dir = config.get('output_directory', 'output')
        os.makedirs(output_dir, exist_ok=True)
        image_path = os.path.join(output_dir, f'temp_{datetime.now().strftime("%Y%m%d%H%M%S")}_{uuid.uuid4().hex[:8]}.jpg')
        with open(image_path, 'wb') as f:
            f.write(image_response.content)

        return image_path

    except Exception as e:
        print(f"Pexels 下载图片失败: {e}")
        return None


def download_pixabay_image(keyword, api_key):
    """从 Pixabay 下载图片"""
    try:
        search_url = 'https://pixabay.com/api/'
        params = {
            'key': api_key,
            'q': keyword,
            'per_page': 3,
            'image_type': 'photo',
            'orientation': 'horizontal'
        }

        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        if not data.get('hits'):
            return None

        image_url = data['hits'][0]['largeImageURL']
        image_response = requests.get(image_url, timeout=10)
        image_response.raise_for_status()

        config = load_config()
        output_dir = config.get('output_directory', 'output')
        os.makedirs(output_dir, exist_ok=True)
        image_path = os.path.join(output_dir, f'temp_{datetime.now().strftime("%Y%m%d%H%M%S")}_{uuid.uuid4().hex[:8]}.jpg')
        with open(image_path, 'wb') as f:
            f.write(image_response.content)

        return image_path

    except Exception as e:
        print(f"Pixabay 下载图片失败: {e}")
        return None


def get_local_image_by_tags(tags=None, config=None):
    """从本地图库中根据标签选择图片"""
    try:
        if not config:
            config = load_config()

        local_dirs = config.get('local_image_directories', [{'path': 'pic', 'tags': ['default']}])

        # 如果指定了标签，优先从匹配标签的目录中选择
        if tags:
            matching_dirs = [d for d in local_dirs if any(tag in d.get('tags', []) for tag in tags)]
            if matching_dirs:
                local_dirs = matching_dirs

        # 收集所有可用的图片
        available_images = []
        for dir_config in local_dirs:
            dir_path = dir_config.get('path', '')
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                for file in os.listdir(dir_path):
                    file_path = os.path.join(dir_path, file)
                    if os.path.isfile(file_path) and file.lower().endswith(tuple(ALLOWED_EXTENSIONS)):
                        available_images.append(file_path)

        # 随机选择一张图片
        if available_images:
            return random.choice(available_images)

        return None

    except Exception as e:
        print(f"从本地图库获取图片失败: {e}")
        return None


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
            if os.path.isfile(file_path) and file.lower().endswith(tuple(ALLOWED_EXTENSIONS)):
                stat = os.stat(file_path)
                images.append({
                    'filename': file,
                    'path': file_path,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                })

    # 按创建时间倒序排列
    images.sort(key=lambda x: x['created'], reverse=True)

    return images


def get_image_with_priority(keyword, config, user_uploaded_path=None):
    """根据优先级策略获取图片（旧版，向后兼容）"""
    # 用户自定义图片具有最高优先级
    if user_uploaded_path and os.path.exists(user_uploaded_path):
        print(f"✓ 使用用户自定义图片: {user_uploaded_path}")
        return user_uploaded_path

    priority = config.get('image_source_priority', ['comfyui', 'user_uploaded', 'pexels', 'unsplash', 'pixabay', 'local'])
    tags = keyword.lower().split() if keyword else []

    for source in priority:
        try:
            if source == 'user_uploaded' and user_uploaded_path:
                if os.path.exists(user_uploaded_path):
                    print(f"使用用户上传的图片: {user_uploaded_path}")
                    return user_uploaded_path

            elif source == 'unsplash':
                unsplash_key = config.get('unsplash_access_key')
                if unsplash_key and keyword:
                    print(f"尝试从 Unsplash 下载图片，关键词: {keyword}")
                    image_path = download_unsplash_image(keyword, unsplash_key)
                    if image_path:
                        print(f"Unsplash 下载成功: {image_path}")
                        return image_path

            elif source == 'pexels':
                pexels_key = config.get('pexels_api_key')
                if pexels_key and keyword:
                    print(f"尝试从 Pexels 下载图片，关键词: {keyword}")
                    image_path = download_pexels_image(keyword, pexels_key)
                    if image_path:
                        print(f"Pexels 下载成功: {image_path}")
                        return image_path

            elif source == 'pixabay':
                pixabay_key = config.get('pixabay_api_key')
                if pixabay_key and keyword:
                    print(f"尝试从 Pixabay 下载图片，关键词: {keyword}")
                    image_path = download_pixabay_image(keyword, pixabay_key)
                    if image_path:
                        print(f"Pixabay 下载成功: {image_path}")
                        return image_path

            elif source == 'local':
                print(f"尝试从本地图库获取图片，标签: {tags}")
                image_path = get_local_image_by_tags(tags if tags else None, config)
                if image_path:
                    print(f"本地图库选择成功: {image_path}")
                    return image_path

        except Exception as e:
            print(f"图片源 {source} 失败: {e}，尝试下一个...")
            continue

    print("所有图片源都失败，将不使用配图")
    return None


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
