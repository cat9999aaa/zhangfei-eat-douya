"""配置加载和保存功能"""

import os
import json
from .defaults import CONFIG_FILE, DEFAULT_COMFYUI_CONFIG, DEFAULT_GEMINI_IMAGE_CONFIG


def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_config(config):
    """保存配置文件"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_comfyui_settings(config):
    """合并默认设置和用户配置"""
    merged = DEFAULT_COMFYUI_CONFIG.copy()
    if not config:
        return merged

    user_cfg = config.get('comfyui_settings') or {}
    for key, value in user_cfg.items():
        if value is not None:
            merged[key] = value

    # 确保基本类型正确
    merged['queue_size'] = max(1, int(merged.get('queue_size', DEFAULT_COMFYUI_CONFIG['queue_size'])))
    merged['timeout_seconds'] = max(30, int(merged.get('timeout_seconds', DEFAULT_COMFYUI_CONFIG['timeout_seconds'])))
    merged['max_attempts'] = max(1, int(merged.get('max_attempts', DEFAULT_COMFYUI_CONFIG['max_attempts'])))
    merged['enabled'] = bool(merged.get('enabled', DEFAULT_COMFYUI_CONFIG['enabled']))
    merged['seed'] = int(merged.get('seed', DEFAULT_COMFYUI_CONFIG['seed']))
    merged['workflow_path'] = merged.get('workflow_path', DEFAULT_COMFYUI_CONFIG['workflow_path'])

    return merged


def get_gemini_image_settings(config):
    """获取 Gemini 图像生成配置"""
    merged = DEFAULT_GEMINI_IMAGE_CONFIG.copy()
    if not config:
        return merged

    user_cfg = config.get('gemini_image_settings') or {}
    for key, value in user_cfg.items():
        if value is not None:
            merged[key] = value

    # 确保基本类型正确
    merged['enabled'] = bool(merged.get('enabled', DEFAULT_GEMINI_IMAGE_CONFIG['enabled']))
    merged['max_retries'] = max(1, int(merged.get('max_retries', DEFAULT_GEMINI_IMAGE_CONFIG['max_retries'])))
    merged['timeout'] = max(10, int(merged.get('timeout', DEFAULT_GEMINI_IMAGE_CONFIG['timeout'])))

    # 如果没有配置独立的 API Key，尝试使用通用的 Gemini API Key
    if not merged.get('api_key'):
        merged['api_key'] = config.get('gemini_api_key', '')

    # 如果没有配置独立的 Base URL，尝试使用通用的 Gemini Base URL
    if not merged.get('base_url'):
        merged['base_url'] = config.get('gemini_base_url', DEFAULT_GEMINI_IMAGE_CONFIG['base_url'])

    return merged
