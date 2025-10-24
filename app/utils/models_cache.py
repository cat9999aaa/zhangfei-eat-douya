"""模型列表缓存管理"""

import os
import json
from datetime import datetime
from pathlib import Path

CACHE_FILE = 'models_cache.json'


def get_cache_file_path():
    """获取缓存文件路径"""
    return Path(CACHE_FILE)


def load_cache():
    """加载缓存数据"""
    cache_path = get_cache_file_path()

    if not cache_path.exists():
        return {
            'gemini_models': {
                'last_updated': None,
                'models': []
            },
            'gemini_image_models': {
                'last_updated': None,
                'models': []
            }
        }

    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载模型缓存失败: {e}")
        return {
            'gemini_models': {
                'last_updated': None,
                'models': []
            },
            'gemini_image_models': {
                'last_updated': None,
                'models': []
            }
        }


def save_cache(cache_data):
    """保存缓存数据"""
    cache_path = get_cache_file_path()

    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"保存模型缓存失败: {e}")
        return False


def update_gemini_models_cache(models):
    """更新 Gemini 主模型缓存"""
    cache = load_cache()
    cache['gemini_models'] = {
        'last_updated': datetime.now().isoformat(),
        'models': models
    }
    return save_cache(cache)


def update_gemini_image_models_cache(models):
    """更新 Gemini 图像模型缓存"""
    cache = load_cache()
    cache['gemini_image_models'] = {
        'last_updated': datetime.now().isoformat(),
        'models': models
    }
    return save_cache(cache)


def get_gemini_models_cache():
    """获取 Gemini 主模型缓存"""
    cache = load_cache()
    return cache.get('gemini_models', {'last_updated': None, 'models': []})


def get_gemini_image_models_cache():
    """获取 Gemini 图像模型缓存"""
    cache = load_cache()
    return cache.get('gemini_image_models', {'last_updated': None, 'models': []})


def clear_cache():
    """清空所有缓存"""
    cache = {
        'gemini_models': {
            'last_updated': None,
            'models': []
        },
        'gemini_image_models': {
            'last_updated': None,
            'models': []
        }
    }
    return save_cache(cache)
