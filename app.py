from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import requests
import os
import json
import re
import subprocess
from datetime import datetime
import uuid
import threading
import random
import time
import copy
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

app = Flask(__name__)
CORS(app)

# 全局任务存储和线程锁
generation_tasks = {}
task_lock = threading.Lock()

# ComfyUI 并发控制
comfyui_lock = threading.Lock()

# 确保基础目录存在（output目录会在配置加载后根据配置创建）
os.makedirs('uploads', exist_ok=True)

# 允许的图片文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}

# 默认的 ComfyUI 配置
DEFAULT_COMFYUI_CONFIG = {
    'enabled': True,
    'server_url': 'http://127.0.0.1:8188',
    'queue_size': 2,
    'timeout_seconds': 180,
    'max_attempts': 2,
    'seed': -1,
    'workflow_path': ''
}

# 预设的视觉模板，用于构建提示词
VISUAL_TEMPLATE_PRESETS = {
    'portrait': {
        'name': '人物特写',
        'positive_prefix': 'ultra detailed cinematic portrait of',
        'positive_suffix': 'sharp focus, 8k, masterpiece, award-winning photography, intricate details, volumetric lighting, high dynamic range',
        'negative': 'lowres, blurry, worst quality, low quality, jpeg artifacts, double face, deformed, cropped, watermark, nsfw'
    },
    'urban_story': {
        'name': '城市纪实',
        'positive_prefix': 'documentary style wide shot of',
        'positive_suffix': 'cinematic storytelling, atmospheric haze, dramatic lighting, realistic photography, depth of field, editorial style, moody ambience',
        'negative': 'lowres, cartoon, painting, illustration, abstract, blurry, distorted, watermark'
    },
    'technology': {
        'name': '科技概念',
        'positive_prefix': 'futuristic concept art of',
        'positive_suffix': 'highly detailed, sleek design, glows, holographic interface, volumetric light, digital art, 8k render, cinematic lighting',
        'negative': 'lowres, blurry, noisy, childlike, hand-drawn, distorted, watermark'
    },
    'nature': {
        'name': '自然风光',
        'positive_prefix': 'breathtaking landscape of',
        'positive_suffix': 'golden hour lighting, ultra realistic, depth of field, atmospheric perspective, highly detailed, award-winning photography',
        'negative': 'lowres, oversaturated, blurry, distorted, extra limbs, watermark, cartoon'
    },
    'editorial': {
        'name': '资讯配图',
        'positive_prefix': 'editorial style illustration of',
        'positive_suffix': 'clean composition, modern infographic aesthetics, vector inspired, balanced color palette, professional magazine layout, sharp details',
        'negative': 'lowres, childish drawing, messy typography, watermark, depressing filter, distorted text'
    },
    'abstract': {
        'name': '抽象概念',
        'positive_prefix': 'abstract conceptual illustration of',
        'positive_suffix': 'minimalist shapes, clean vector art, modern gradients, smooth lighting, design magazine aesthetic, crisp edges, high resolution',
        'negative': 'lowres, messy composition, noisy texture, random clutter, illegible text, watermark'
    }
}
IMAGE_STYLE_TEMPLATES = {
    'custom': {
        'label': '自定义风格',
        'positive': '',
        'negative': ''
    },
    'realistic_photo': {
        'label': '写实摄影',
        'positive': 'highly detailed realistic photography, natural lighting, sharp focus',
        'negative': 'cartoon, illustration, painting, lowres, oversaturated, cgi'
    },
    'cyberpunk': {
        'label': '赛博朋克',
        'positive': 'cyberpunk, neon rain, dramatic lighting, futuristic cityscape',
        'negative': 'lowres, watercolor, sketch, plain background'
    },
    'business': {
        'label': '商务插画',
        'positive': 'business illustration, clean vector style, professional tone, modern minimal branding',
        'negative': 'messy, chaotic, childish, graffiti'
    }
}

# 摘要模型选项将从实时模型列表获取，这里只保留特殊选项
SUMMARY_MODEL_SPECIAL_OPTIONS = ['__default__']



comfyui_runtime = {
    'semaphore': threading.BoundedSemaphore(DEFAULT_COMFYUI_CONFIG['queue_size']),
    'queue_size': DEFAULT_COMFYUI_CONFIG['queue_size'],
    'config': DEFAULT_COMFYUI_CONFIG.copy()
}

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

def update_comfyui_runtime(config):
    """根据配置更新并发控制等运行时参数"""
    settings = get_comfyui_settings(config)
    queue_size = settings.get('queue_size', DEFAULT_COMFYUI_CONFIG['queue_size'])
    with comfyui_lock:
        if queue_size != comfyui_runtime['queue_size']:
            comfyui_runtime['semaphore'] = threading.BoundedSemaphore(queue_size)
            comfyui_runtime['queue_size'] = queue_size
        comfyui_runtime['config'] = settings
    return settings

# 配置文件路径
CONFIG_FILE = 'config.json'

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

# 初始化线程池的函数
def create_executor(max_workers=3):
    global executor
    # 检查现有的 executor 是否需要关闭
    if 'executor' in globals() and executor:
        executor.shutdown(wait=False)
    executor = ThreadPoolExecutor(max_workers=max_workers)

# 应用程序启动时创建线程池
config = load_config()
initial_workers = config.get('max_concurrent_tasks', 3)
create_executor(initial_workers)
update_comfyui_runtime(config)

@app.route('/')
def index():
    """渲染写作页面"""
    return render_template('write.html')

@app.route('/config')
def config_page():
    """渲染配置页面"""
    return render_template('config.html')

@app.route('/history')
def history_page():
    """渲染历史记录页面"""
    return render_template('history.html')

@app.route('/api/test-unsplash', methods=['POST'])
def test_unsplash():
    """测试 Unsplash API 配置"""
    data = request.json
    access_key = data.get('access_key', '')

    if not access_key:
        return jsonify({'success': False, 'error': '请提供 Access Key'}), 400

    try:
        # 搜索一张测试图片
        search_url = 'https://api.unsplash.com/search/photos'
        headers = {'Authorization': f'Client-ID {access_key}'}
        params = {'query': 'nature', 'per_page': 1}

        response = requests.get(search_url, headers=headers, params=params, timeout=10)

        if response.status_code == 401:
            return jsonify({'success': False, 'error': 'Access Key 无效或已过期'})
        elif response.status_code == 403:
            return jsonify({'success': False, 'error': '请求频率超限，请稍后再试'})

        response.raise_for_status()
        data = response.json()

        if data.get('results') and len(data['results']) > 0:
            image_url = data['results'][0]['urls']['small']
            return jsonify({
                'success': True,
                'image_url': image_url,
                'message': 'Unsplash API 工作正常'
            })
        else:
            return jsonify({'success': False, 'error': '未找到测试图片'})

    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': '请求超时，可能是网络问题'})
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': '无法连接到 Unsplash API，请检查网络'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'测试失败: {str(e)}'})

@app.route('/api/test-pexels', methods=['POST'])
def test_pexels():
    """测试 Pexels API 配置"""
    data = request.json
    api_key = data.get('api_key', '')

    if not api_key:
        return jsonify({'success': False, 'error': '请提供 API Key'}), 400

    try:
        search_url = 'https://api.pexels.com/v1/search'
        headers = {'Authorization': api_key}
        params = {'query': 'nature', 'per_page': 1}

        response = requests.get(search_url, headers=headers, params=params, timeout=10)

        if response.status_code == 401:
            return jsonify({'success': False, 'error': 'API Key 无效或已过期'})
        elif response.status_code == 403:
            return jsonify({'success': False, 'error': '请求频率超限，请稍后再试'})

        response.raise_for_status()
        data = response.json()

        if data.get('photos') and len(data['photos']) > 0:
            image_url = data['photos'][0]['src']['small']
            return jsonify({
                'success': True,
                'image_url': image_url,
                'message': 'Pexels API 工作正常'
            })
        else:
            return jsonify({'success': False, 'error': '未找到测试图片'})

    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': '请求超时，可能是网络问题'})
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': '无法连接到 Pexels API，请检查网络'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'测试失败: {str(e)}'})

@app.route('/api/test-pixabay', methods=['POST'])
def test_pixabay():
    """测试 Pixabay API 配置"""
    data = request.json
    api_key = data.get('api_key', '')

    if not api_key:
        return jsonify({'success': False, 'error': '请提供 API Key'}), 400

    try:
        search_url = 'https://pixabay.com/api/'
        params = {'key': api_key, 'q': 'nature', 'per_page': 3}

        response = requests.get(search_url, params=params, timeout=10)

        if response.status_code == 401 or response.status_code == 400:
            return jsonify({'success': False, 'error': 'API Key 无效或已过期'})

        response.raise_for_status()
        data = response.json()

        if data.get('hits') and len(data['hits']) > 0:
            image_url = data['hits'][0]['webformatURL']
            return jsonify({
                'success': True,
                'image_url': image_url,
                'message': 'Pixabay API 工作正常'
            })
        else:
            return jsonify({'success': False, 'error': '未找到测试图片'})

    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': '请求超时，可能是网络问题'})
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': '无法连接到 Pixabay API，请检查网络'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'测试失败: {str(e)}'})


@app.route('/api/test-comfyui', methods=['POST'])
def test_comfyui():
    """测试 ComfyUI Workflow 配置"""
    data = request.json or {}
    try:
        config = load_config()
        if data.get('comfyui_settings'):
            settings = get_comfyui_settings({'comfyui_settings': data['comfyui_settings']})
        else:
            settings = get_comfyui_settings(config)

        if not settings.get('enabled', True):
            return jsonify({'success': False, 'error': '请先启用 ComfyUI 自动生成'}), 400

        prompts = {
            'template': 'test',
            'positive_prompt': data.get('positive_prompt', 'cinematic concept art, ultra detailed, high quality render'),
            'negative_prompt': data.get('negative_prompt', 'lowres, blurry, bad anatomy, watermark')
        }

        temp_config = dict(config)
        temp_config['comfyui_settings'] = settings
        if 'comfyui_positive_style' in data:
            temp_config['comfyui_positive_style'] = data.get('comfyui_positive_style', '')
        if 'comfyui_negative_style' in data:
            temp_config['comfyui_negative_style'] = data.get('comfyui_negative_style', '')
        image_path, metadata = generate_image_with_comfyui(
            topic=data.get('topic', 'comfyui_test'),
            prompts=prompts,
            blueprint=None,
            config=temp_config,
            settings_override=settings,
            test_mode=True
        )

        if image_path:
            return jsonify({
                'success': True,
                'image_path': image_path,
                'metadata': metadata
            })

        error_message = '生成失败'
        if metadata.get('errors'):
            error_message = metadata['errors'][-1]

        return jsonify({'success': False, 'error': error_message})

    except Exception as e:
        return jsonify({'success': False, 'error': f'测试失败: {str(e)}'}), 500


@app.route('/api/check-pandoc', methods=['GET'])
def check_pandoc():
    """检查 Pandoc 配置状态"""
    config = load_config()
    pandoc_path = config.get('pandoc_path', '')
    return jsonify({
        'pandoc_configured': bool(pandoc_path),
        'pandoc_path': pandoc_path if pandoc_path else None
    })

@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    """用户上传图片"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': '未选择文件'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'success': False, 'error': '未选择文件'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': '不支持的文件格式，仅支持 png, jpg, jpeg, gif, webp, bmp'}), 400

    try:
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        # 添加时间戳避免重名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        safe_filename = f"{name}_{timestamp}{ext}"

        # 保存到 uploads 目录
        config = load_config()
        upload_dir = config.get('uploaded_images_dir', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, safe_filename)

        file.save(filepath)

        return jsonify({
            'success': True,
            'filename': safe_filename,
            'path': filepath,
            'message': '图片上传成功'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f'上传失败: {str(e)}'}), 500

@app.route('/api/list-local-images', methods=['GET'])
def list_local_images():
    """列出本地图库中的所有图片"""
    try:
        config = load_config()
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

        return jsonify({'success': True, 'images': images, 'total': len(images)})

    except Exception as e:
        return jsonify({'success': False, 'error': f'获取图片列表失败: {str(e)}'}), 500

@app.route('/api/list-uploaded-images', methods=['GET'])
def list_uploaded_images():
    """列出用户上传的所有图片"""
    try:
        config = load_config()
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

        return jsonify({'success': True, 'images': images, 'total': len(images)})

    except Exception as e:
        return jsonify({'success': False, 'error': f'获取上传图片列表失败: {str(e)}'}), 500

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """处理配置的获取和保存"""
    if request.method == 'GET':
        config = load_config()
        # 返回配置状态，不返回实际的密钥
        return jsonify({
            'gemini_api_key_set': bool(config.get('gemini_api_key')),
            'unsplash_access_key_set': bool(config.get('unsplash_access_key')),
            'pexels_api_key_set': bool(config.get('pexels_api_key')),
            'pixabay_api_key_set': bool(config.get('pixabay_api_key')),
            'gemini_base_url': config.get('gemini_base_url', 'https://generativelanguage.googleapis.com'),
            'pandoc_path': config.get('pandoc_path', ''),
            'default_model': config.get('default_model', 'gemini-pro'),
            'default_prompt': config.get('default_prompt', ''),
            'max_concurrent_tasks': config.get('max_concurrent_tasks', 3),
            'image_source_priority': config.get('image_source_priority', ['comfyui', 'user_uploaded', 'pexels', 'unsplash', 'pixabay', 'local']),
            'local_image_directories': config.get('local_image_directories', [{'path': 'pic', 'tags': ['default']}]),
            'enable_user_upload': config.get('enable_user_upload', True),
            'uploaded_images_dir': config.get('uploaded_images_dir', 'uploads'),
            'output_directory': config.get('output_directory', 'output'),
            'comfyui_settings': get_comfyui_settings(config),
            'comfyui_positive_style': config.get('comfyui_positive_style', ''),
            'comfyui_negative_style': config.get('comfyui_negative_style', ''),
            'comfyui_image_count': config.get('comfyui_image_count', 1),
            'comfyui_style_template': config.get('comfyui_style_template', 'custom'),
            'comfyui_summary_model': config.get('comfyui_summary_model', '__default__'),
            'comfyui_style_templates': [
                { 'id': key, 'label': value['label'] }
                for key, value in IMAGE_STYLE_TEMPLATES.items()
            ]
        })

    elif request.method == 'POST':
        new_config = request.json
        old_config = load_config()

        # 合并配置：如果新配置中没有提供密钥，使用旧的
        final_config = {
            'gemini_base_url': new_config.get('gemini_base_url', 'https://generativelanguage.googleapis.com'),
            'pandoc_path': new_config.get('pandoc_path', ''),
            'default_model': new_config.get('default_model', 'gemini-pro'),
            'default_prompt': new_config.get('default_prompt', ''),
            'max_concurrent_tasks': int(new_config.get('max_concurrent_tasks', old_config.get('max_concurrent_tasks', 3))),
            'image_source_priority': new_config.get('image_source_priority', old_config.get('image_source_priority', ['comfyui', 'user_uploaded', 'pexels', 'unsplash', 'pixabay', 'local'])),
            'local_image_directories': new_config.get('local_image_directories', old_config.get('local_image_directories', [{'path': 'pic', 'tags': ['default']}])) ,
            'enable_user_upload': new_config.get('enable_user_upload', old_config.get('enable_user_upload', True)),
            'uploaded_images_dir': new_config.get('uploaded_images_dir', old_config.get('uploaded_images_dir', 'uploads')) ,
            'output_directory': new_config.get('output_directory', old_config.get('output_directory', 'output')),
            'comfyui_positive_style': new_config.get('comfyui_positive_style', old_config.get('comfyui_positive_style', '')),
            'comfyui_negative_style': new_config.get('comfyui_negative_style', old_config.get('comfyui_negative_style', '')),
            'comfyui_image_count': int(new_config.get('comfyui_image_count', old_config.get('comfyui_image_count', 1))),
            'comfyui_style_template': new_config.get('comfyui_style_template', old_config.get('comfyui_style_template', 'custom')),
            'comfyui_summary_model': new_config.get('comfyui_summary_model', old_config.get('comfyui_summary_model', '__default__'))
        }

        # 处理 API 密钥
        if new_config.get('gemini_api_key'):
            final_config['gemini_api_key'] = new_config['gemini_api_key']
        elif old_config.get('gemini_api_key'):
            final_config['gemini_api_key'] = old_config['gemini_api_key']

        if new_config.get('unsplash_access_key'):
            final_config['unsplash_access_key'] = new_config['unsplash_access_key']
        elif old_config.get('unsplash_access_key'):
            final_config['unsplash_access_key'] = old_config['unsplash_access_key']

        if new_config.get('pexels_api_key'):
            final_config['pexels_api_key'] = new_config['pexels_api_key']
        elif old_config.get('pexels_api_key'):
            final_config['pexels_api_key'] = old_config['pexels_api_key']

        if new_config.get('pixabay_api_key'):
            final_config['pixabay_api_key'] = new_config['pixabay_api_key']
        elif old_config.get('pixabay_api_key'):
            final_config['pixabay_api_key'] = old_config['pixabay_api_key']

        # 处理 ComfyUI 配置
        comfy_settings_payload = new_config.get('comfyui_settings')
        if comfy_settings_payload is None:
            comfy_settings_payload = old_config.get('comfyui_settings', {})
        final_config['comfyui_settings'] = get_comfyui_settings({'comfyui_settings': comfy_settings_payload})

        if final_config['comfyui_image_count'] not in (1, 3):
            final_config['comfyui_image_count'] = 1

        if final_config['comfyui_style_template'] not in IMAGE_STYLE_TEMPLATES:
            final_config['comfyui_style_template'] = 'custom'

        # 摘要模型验证：允许 __default__ 或任何字符串（因为模型列表是动态的）
        if not final_config['comfyui_summary_model']:
            final_config['comfyui_summary_model'] = '__default__'

        save_config(final_config)
        # 更新线程池大小
        create_executor(final_config.get('max_concurrent_tasks', 3))
        update_comfyui_runtime(final_config)
        return jsonify({'success': True, 'message': '配置保存成功'})

@app.route('/api/models')
def get_models():
    """获取可用的 Gemini 模型列表"""
    config = load_config()
    api_key = config.get('gemini_api_key', '')
    base_url = config.get('gemini_base_url', 'https://generativelanguage.googleapis.com')

    if not api_key:
        return jsonify({'error': '请先配置 Gemini API Key'}), 400

    try:
        # 使用 HTTP 请求获取模型列表
        url = f'{base_url}/v1beta/models?key={api_key}'
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        model_list = []
        for model in data.get('models', []):
            if 'generateContent' in model.get('supportedGenerationMethods', []):
                model_list.append({
                    'name': model.get('name', '').replace('models/', ''),
                    'display_name': model.get('displayName', model.get('name', ''))
                })
        return jsonify({'models': model_list})
    except Exception as e:
        return jsonify({'error': f'获取模型列表失败: {str(e)}'}), 500

@app.route('/api/test-model', methods=['POST'])
def test_model():
    """测试 Gemini 模型"""
    data = request.json
    model_name = data.get('model_name', '')
    api_key = data.get('api_key', '')
    base_url = data.get('base_url', 'https://generativelanguage.googleapis.com')

    if not model_name:
        return jsonify({'success': False, 'error': '请提供模型名称'}), 400

    # 如果没有提供API Key，尝试从配置加载
    if not api_key:
        config = load_config()
        api_key = config.get('gemini_api_key', '')
        if not api_key:
            return jsonify({'success': False, 'error': '请先配置 Gemini API Key'}), 400

    try:
        # 使用简单的测试提示词
        test_prompt = "请用一句话介绍你自己。"

        url = f'{base_url}/v1beta/models/{model_name}:generateContent?key={api_key}'
        headers = {'Content-Type': 'application/json'}
        payload = {
            'contents': [{
                'parts': [{'text': test_prompt}]
            }]
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code == 401:
            return jsonify({'success': False, 'error': 'API Key 无效或已过期'})
        elif response.status_code == 403:
            return jsonify({'success': False, 'error': '权限不足或配额已用完'})
        elif response.status_code == 404:
            return jsonify({'success': False, 'error': f'模型 {model_name} 不存在'})

        response.raise_for_status()

        result = response.json()

        if 'candidates' in result and len(result['candidates']) > 0:
            reply = result['candidates'][0]['content']['parts'][0]['text']
            return jsonify({
                'success': True,
                'message': '模型测试成功',
                'reply': reply[:100] + ('...' if len(reply) > 100 else '')
            })
        else:
            return jsonify({'success': False, 'error': '模型返回了空响应'})

    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': '请求超时，请检查网络连接'})
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': '无法连接到 API 服务器，请检查 Base URL 和网络'})
    except requests.exceptions.HTTPError as e:
        return jsonify({'success': False, 'error': f'HTTP 错误: {str(e)}'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'测试失败: {str(e)}'})

def get_image_with_priority(keyword, config, user_uploaded_path=None):
    """根据优先级策略获取图片"""
    # 用户自定义图片具有最高优先级，直接返回
    if user_uploaded_path and os.path.exists(user_uploaded_path):
        print(f"✓ 使用用户自定义图片: {user_uploaded_path}")
        return user_uploaded_path

    priority = config.get('image_source_priority', ['comfyui', 'user_uploaded', 'pexels', 'unsplash', 'pixabay', 'local'])

    # 提取关键词的标签（用于本地图库匹配）
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

def resolve_image_with_priority(keyword, config, user_uploaded_path=None, visual_prompts=None, blueprint=None, topic=None):
    """扩展版的图片获取逻辑，支持 ComfyUI 自动生成并返回元数据"""
    comfy_settings = get_comfyui_settings(config)

    if user_uploaded_path and os.path.exists(user_uploaded_path):
        print(f"✓ 使用用户自定义图片: {user_uploaded_path}")
        return user_uploaded_path, 'user_uploaded', {}

    default_priority = ['comfyui', 'user_uploaded', 'pexels', 'unsplash', 'pixabay', 'local']
    priority = config.get('image_source_priority', default_priority)
    if comfy_settings.get('enabled', True) and 'comfyui' not in priority:
        priority = ['comfyui'] + [src for src in priority if src != 'comfyui']

    tags = keyword.lower().split() if keyword else []

    for source in priority:
        try:
            if source == 'comfyui':
                if visual_prompts and topic:
                    workflow_path = comfy_settings.get('workflow_path')
                    if not workflow_path:
                        print("ComfyUI 未配置 workflow_path，跳过")
                        continue
                    image_path, metadata = generate_image_with_comfyui(
                        topic,
                        visual_prompts,
                        blueprint,
                        config,
                        settings_override=comfy_settings
                    )
                    if image_path:
                        print(f"ComfyUI 生成成功: {image_path}")
                        return image_path, 'comfyui', metadata
                else:
                    print("缺少 ComfyUI 所需的 prompt 信息，跳过")

            elif source == 'user_uploaded' and user_uploaded_path:
                if os.path.exists(user_uploaded_path):
                    print(f"使用用户上传的图片: {user_uploaded_path}")
                    return user_uploaded_path, 'user_uploaded', {}

            elif source == 'unsplash':
                unsplash_key = config.get('unsplash_access_key')
                if unsplash_key and keyword:
                    print(f"尝试从 Unsplash 下载图片，关键词: {keyword}")
                    image_path = download_unsplash_image(keyword, unsplash_key)
                    if image_path:
                        print(f"Unsplash 下载成功: {image_path}")
                        return image_path, 'unsplash', {}

            elif source == 'pexels':
                pexels_key = config.get('pexels_api_key')
                if pexels_key and keyword:
                    print(f"尝试从 Pexels 下载图片，关键词: {keyword}")
                    image_path = download_pexels_image(keyword, pexels_key)
                    if image_path:
                        print(f"Pexels 下载成功: {image_path}")
                        return image_path, 'pexels', {}

            elif source == 'pixabay':
                pixabay_key = config.get('pixabay_api_key')
                if pixabay_key and keyword:
                    print(f"尝试从 Pixabay 下载图片，关键词: {keyword}")
                    image_path = download_pixabay_image(keyword, pixabay_key)
                    if image_path:
                        print(f"Pixabay 下载成功: {image_path}")
                        return image_path, 'pixabay', {}

            elif source == 'local':
                print(f"尝试从本地图库获取图片，标签: {tags}")
                image_path = get_local_image_by_tags(tags if tags else None, config)
                if image_path:
                    print(f"本地图库选择成功: {image_path}")
                    return image_path, 'local', {}

        except Exception as e:
            print(f"图片源 {source} 失败: {e}，尝试下一项...")
            continue

    print("所有图片源都失败，将不使用配图")
    return None, 'none', {}

def _execute_single_article_generation(topic, config, user_uploaded_images=None):
    """为单个主题生成文章（将在后台线程中执行）

    Args:
        topic: 文章主题
        config: 配置对象
        user_uploaded_images: 用户上传的图片列表(数组格式),每项包含 {type, path, order}
    """
    gemini_api_key = config.get('gemini_api_key', '')
    gemini_base_url = config.get('gemini_base_url', 'https://generativelanguage.googleapis.com')
    pandoc_path = config.get('pandoc_path', '')
    model_name = config.get('default_model') or 'gemini-pro'
    custom_prompt = config.get('default_prompt', '')
    enable_image = config.get('enable_image', True)

    # 获取目标图片数量
    target_image_count = config.get('comfyui_image_count', 1)

    # 兼容旧格式:将单个图片转为数组
    if user_uploaded_images and not isinstance(user_uploaded_images, list):
        user_uploaded_images = [user_uploaded_images]

    # 1. 使用 Gemini 生成文章
    article = generate_article_with_gemini(topic, gemini_api_key, gemini_base_url, model_name, custom_prompt)
    article_title = extract_article_title(article)

    # 2. 提取段落结构
    paragraphs = extract_paragraph_structures(article)

    # 3. 计算图片插入位置
    image_slots = compute_image_slots(paragraphs, target_image_count)

    # 4. 收集所有图片信息
    image_list = []
    images_metadata = []

    if enable_image:
        # 确定需要生成多少张图片
        user_image_count = len(user_uploaded_images) if user_uploaded_images else 0
        need_generate_count = target_image_count - user_image_count

        # 先使用用户上传的图片
        for i, user_img in enumerate(user_uploaded_images or []):
            if i < len(image_slots):
                summary = user_img.get('summary', '配图')
                image_list.append({
                    'path': user_img.get('path'),
                    'summary': summary,
                    'paragraph_index': image_slots[i],
                    'source': 'user_uploaded',
                    'order': i
                })
                images_metadata.append({
                    'source': 'user_uploaded',
                    'path': user_img.get('path'),
                    'order': i
                })

        # 如果还需要更多图片,自动生成
        if need_generate_count > 0:
            try:
                # 生成视觉蓝图(仅一次)
                visual_blueprint = generate_visual_blueprint(topic, article, gemini_api_key, gemini_base_url, model_name)
                visual_prompts = build_visual_prompts(visual_blueprint)
                image_keyword = derive_keyword_from_blueprint(visual_blueprint)
            except Exception as e:
                print(f"生成视觉蓝图失败: {e}")
                visual_blueprint = None
                visual_prompts = None
                image_keyword = ''

            # 为每个需要生成的图片位置生成图片
            for i in range(user_image_count, target_image_count):
                try:
                    slot_index = image_slots[i] if i < len(image_slots) else None

                    # 为该段落生成摘要
                    if slot_index is not None and slot_index < len(paragraphs):
                        para_text = paragraphs[slot_index]['text']
                        para_summary = summarize_paragraph_for_image(para_text, topic, config)
                    else:
                        para_summary = f"visual representation of {topic}"

                    # 使用段落摘要作为主要内容，视觉蓝图作为辅助
                    # 注意：段落摘要应该是最重要的，放在最前面
                    if visual_prompts:
                        # 从视觉蓝图中提取一些通用描述（不包括具体主题）
                        blueprint_style = visual_prompts.get('positive_prompt', '')
                        # 段落摘要 + 通用风格描述
                        custom_prompts = {
                            'positive_prompt': para_summary,  # 段落摘要作为主体
                            'negative_prompt': visual_prompts.get('negative_prompt', 'lowres, blurry, watermark')
                        }
                    else:
                        custom_prompts = {
                            'positive_prompt': para_summary,
                            'negative_prompt': 'lowres, blurry, watermark'
                        }

                    # 生成图片
                    image_path, image_source, image_metadata = resolve_image_with_priority(
                        image_keyword,
                        config,
                        None,  # 不使用用户上传图片
                        custom_prompts,
                        visual_blueprint,
                        topic
                    )

                    if image_path:
                        image_list.append({
                            'path': image_path,
                            'summary': para_summary,
                            'paragraph_index': slot_index,
                            'source': image_source,
                            'order': i
                        })
                        images_metadata.append({
                            'source': image_source,
                            'path': image_path,
                            'summary': para_summary,
                            'paragraph_index': slot_index,
                            'order': i,
                            'metadata': image_metadata
                        })
                        print(f"✓ 第 {i+1} 张图片生成成功: {image_path}")
                    else:
                        print(f"✗ 第 {i+1} 张图片生成失败,跳过")
                        images_metadata.append({
                            'source': 'failed',
                            'order': i,
                            'error': '生成失败'
                        })
                except Exception as e:
                    print(f"✗ 第 {i+1} 张图片生成异常: {e}")
                    images_metadata.append({
                        'source': 'error',
                        'order': i,
                        'error': str(e)
                    })

    # 5. 生成 Word 文档(使用新的多图插入方式)
    filename = create_word_document(article_title, article, image_list, enable_image, pandoc_path, config)

    return {
        'success': True,
        'topic': topic,
        'article_title': article_title,
        'filename': filename,
        'image_count': len(image_list),
        'images_info': images_metadata,
        'has_image': len(image_list) > 0
    }

def _execute_generation_task(task_id, topics, config):
    """后台任务执行函数 - 并行处理"""
    total_topics = len(topics)

    # 获取主题图片映射
    with task_lock:
        task = generation_tasks.get(task_id, {})
        topic_images = task.get('topic_images', {})

    # 使用 futures 来跟踪每个主题的生成任务
    with ThreadPoolExecutor(max_workers=config.get('max_concurrent_tasks', 3)) as single_task_executor:
        futures = {}
        for topic in topics:
            # 获取该主题对应的图片信息并转换为数组格式
            topic_image_info = topic_images.get(topic)
            user_uploaded_images = []

            if topic_image_info:
                # 兼容旧格式:将单个图片对象转为数组
                if isinstance(topic_image_info, dict):
                    # 单个图片对象
                    if topic_image_info.get('type') == 'uploaded':
                        user_uploaded_images.append({
                            'type': 'uploaded',
                            'path': topic_image_info.get('path'),
                            'summary': topic_image_info.get('summary', '配图'),
                            'order': 0
                        })
                    elif topic_image_info.get('type') == 'url':
                        # 如果是URL，需要先下载
                        url = topic_image_info.get('url')
                        try:
                            response = requests.get(url, timeout=10)
                            response.raise_for_status()

                            # 保存临时文件
                            ext = url.split('.')[-1].lower()
                            if ext not in ALLOWED_EXTENSIONS:
                                ext = 'jpg'
                            output_dir = config.get('output_directory', 'output')
                            os.makedirs(output_dir, exist_ok=True)
                            temp_path = os.path.join(output_dir, f'temp_url_{datetime.now().strftime("%Y%m%d%H%M%S")}_{uuid.uuid4().hex[:8]}.{ext}')
                            with open(temp_path, 'wb') as f:
                                f.write(response.content)
                            user_uploaded_images.append({
                                'type': 'uploaded',
                                'path': temp_path,
                                'summary': topic_image_info.get('summary', '配图'),
                                'order': 0
                            })
                        except Exception as e:
                            print(f"下载URL图片失败 ({topic}): {e}")
                elif isinstance(topic_image_info, list):
                    # 已经是数组格式，直接使用
                    for idx, img in enumerate(topic_image_info):
                        if img.get('type') == 'uploaded':
                            user_uploaded_images.append({
                                'type': 'uploaded',
                                'path': img.get('path'),
                                'summary': img.get('summary', '配图'),
                                'order': img.get('order', idx)
                            })
                        elif img.get('type') == 'url':
                            # 下载URL图片
                            url = img.get('url')
                            try:
                                response = requests.get(url, timeout=10)
                                response.raise_for_status()

                                ext = url.split('.')[-1].lower()
                                if ext not in ALLOWED_EXTENSIONS:
                                    ext = 'jpg'
                                output_dir = config.get('output_directory', 'output')
                                os.makedirs(output_dir, exist_ok=True)
                                temp_path = os.path.join(output_dir, f'temp_url_{datetime.now().strftime("%Y%m%d%H%M%S")}_{uuid.uuid4().hex[:8]}.{ext}')
                                with open(temp_path, 'wb') as f:
                                    f.write(response.content)
                                user_uploaded_images.append({
                                    'type': 'uploaded',
                                    'path': temp_path,
                                    'summary': img.get('summary', '配图'),
                                    'order': img.get('order', idx)
                                })
                            except Exception as e:
                                print(f"下载URL图片失败 ({topic}, 第{idx+1}张): {e}")

            futures[single_task_executor.submit(_execute_single_article_generation, topic, config, user_uploaded_images)] = topic

        for future in as_completed(futures):
            topic = futures[future]
            try:
                result = future.result()
                with task_lock:
                    task = generation_tasks[task_id]
                    task['results'].append(result)
                    print(f"✓ 文章生成成功: {topic}")
                    print(f"  当前结果数: {len(task['results'])}, 错误数: {len(task['errors'])}")

            except Exception as e:
                with task_lock:
                    task = generation_tasks[task_id]
                    task['errors'].append({'topic': topic, 'error': str(e)})
                    print(f"✗ 文章生成失败: {topic} - {str(e)}")
                    print(f"  当前结果数: {len(task['results'])}, 错误数: {len(task['errors'])}")

            finally:
                with task_lock:
                    task = generation_tasks[task_id]
                    completed_count = len(task['results']) + len(task['errors'])
                    # 使用任务的total字段，而不是局部的total_topics
                    task_total = task.get('total', len(topics))
                    task['progress'] = (completed_count / task_total) * 100 if task_total > 0 else 0
                    print(f"  进度更新: {completed_count}/{task_total} = {task['progress']:.1f}%")

        # 所有任务完成后，设置状态为completed
        with task_lock:
            task = generation_tasks[task_id]
            completed_count = len(task['results']) + len(task['errors'])
            if completed_count >= task.get('total', 0):
                task['status'] = 'completed'
                print(f"✓ 任务完成! 总结果: {len(task['results'])} 成功, {len(task['errors'])} 失败")

@app.route('/api/download-image-from-url', methods=['POST'])
def download_image_from_url():
    """从URL下载图片到服务器"""
    data = request.json
    url = data.get('url', '')

    if not url:
        return jsonify({'success': False, 'error': '请提供图片URL'}), 400

    try:
        # 下载图片
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # 验证是否为图片
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            return jsonify({'success': False, 'error': 'URL不是有效的图片'}), 400

        # 生成文件名
        ext = content_type.split('/')[-1]
        if ext not in ALLOWED_EXTENSIONS:
            ext = 'jpg'

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'url_image_{timestamp}_{uuid.uuid4().hex[:8]}.{ext}'

        # 保存到 uploads 目录
        upload_dir = load_config().get('uploaded_images_dir', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(response.content)

        return jsonify({
            'success': True,
            'filename': filename,
            'path': filepath,
            'message': '图片下载成功'
        })

    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': '下载超时'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'error': f'下载失败: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'处理失败: {str(e)}'}), 500

@app.route('/api/generate', methods=['POST'])
def generate_article():
    """启动文章生成任务"""
    data = request.json
    topics = data.get('topics', [])
    topic_images = data.get('topic_images', {})  # {topic: {type, url/path}}

    if not topics:
        return jsonify({'error': '请提供至少一个主题'}), 400

    config = load_config()
    if not config.get('gemini_api_key'):
        return jsonify({'error': '请先配置 Gemini API Key'}), 400
    if not config.get('pandoc_path'):
        return jsonify({'error': '请先在配置页面设置 Pandoc 可执行文件路径！'}), 400

    task_id = str(uuid.uuid4())
    with task_lock:
        generation_tasks[task_id] = {
            'status': 'running',
            'progress': 0,
            'results': [],
            'errors': [],
            'total': len(topics),
            'topic_images': topic_images  # 保存图片映射
        }

    # 提交到线程池执行
    executor.submit(_execute_generation_task, task_id, topics, config)

    return jsonify({'success': True, 'task_id': task_id})

def generate_article_with_gemini(topic, api_key, base_url, model_name, custom_prompt=''):
    """使用 Gemini API 生成文章"""
    # 使用自定义 prompt 或默认 prompt
    if custom_prompt:
        prompt = custom_prompt.replace('{topic}', topic)
    else:
        prompt = f"""请根据以下标题或内容写一篇详细的文章：

{topic}

要求：
1. 第一行必须是文章的标题，使用 # 标记（Markdown 格式）
2. 文章要有明确的结构，使用 ## 标记小标题
3. 内容要详实、有深度
4. 字数在 800-1200 字之间
5. 使用中文写作
6. 语言流畅自然
7. 可以使用 Markdown 格式（如 #、##、**等）来组织文章结构

请直接开始写文章，不需要额外的说明。"""

    # 使用 HTTP 请求调用 Gemini API
    url = f'{base_url}/v1beta/models/{model_name}:generateContent?key={api_key}'
    headers = {'Content-Type': 'application/json'}
    data = {
        'contents': [{
            'parts': [{'text': prompt}]
        }]
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    result = response.json()
    if 'candidates' in result and len(result['candidates']) > 0:
        return result['candidates'][0]['content']['parts'][0]['text']
    else:
        raise Exception('无法从 API 响应中提取文章内容')

def extract_article_title(article):
    """从文章内容中提取标题（第一行或第一段）"""
    lines = article.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line:
            # 去除 Markdown 标记
            title = re.sub(r'^#+\s*', '', line)
            title = re.sub(r'\*\*(.*?)\*\*', r'\1', title)
            title = re.sub(r'\*(.*?)\*', r'\1', title)
            return title.strip()
    return "未命名文章"

def extract_image_keyword(article, api_key, base_url, model_name):
    """从文章中提取最适合的图片搜索关键词"""
    prompt = f"""请阅读以下文章，提取一个最适合作为配图的英文关键词或短语（2-4个单词）。
这个关键词应该能代表文章的核心主题，适合在图片库中搜索。

文章内容：
{article[:500]}...

请只返回英文关键词或短语，不要有其他内容。例如："mountain landscape" 或 "technology innovation"。"""

    # 使用 HTTP 请求调用 Gemini API
    url = f'{base_url}/v1beta/models/{model_name}:generateContent?key={api_key}'
    headers = {'Content-Type': 'application/json'}
    data = {
        'contents': [{
            'parts': [{'text': prompt}]
        }]
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    result = response.json()
    if 'candidates' in result and len(result['candidates']) > 0:
        keyword = result['candidates'][0]['content']['parts'][0]['text']
        keyword = keyword.strip().strip('"').strip("'")
        return keyword
    else:
        raise Exception('无法从 API 响应中提取关键词')

def download_unsplash_image(keyword, access_key):
    """从 Unsplash 下载图片"""
    try:
        # 搜索图片
        search_url = 'https://api.unsplash.com/search/photos'
        headers = {'Authorization': f'Client-ID {access_key}'}
        params = {'query': keyword, 'per_page': 1, 'orientation': 'landscape'}

        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        if not data['results']:
            return None

        # 获取第一张图片的下载链接
        image_url = data['results'][0]['urls']['regular']

        # 下载图片
        image_response = requests.get(image_url, timeout=10)
        image_response.raise_for_status()

        # 保存到临时位置
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

        # 获取第一张图片的下载链接（中等尺寸）
        image_url = data['photos'][0]['src']['large']

        # 下载图片
        image_response = requests.get(image_url, timeout=10)
        image_response.raise_for_status()

        # 保存到临时位置
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

        # 获取第一张图片的下载链接
        image_url = data['hits'][0]['largeImageURL']

        # 下载图片
        image_response = requests.get(image_url, timeout=10)
        image_response.raise_for_status()

        # 保存到临时位置
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

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_word_document(title, content, image_list=None, enable_image=True, pandoc_path='pandoc', config=None):
    """使用 pandoc 将 Markdown 转换为 Word 文档

    Args:
        title: 文章标题
        content: Markdown内容
        image_list: 图片列表，每项包含 {'path', 'summary', 'paragraph_index'}
                   为了向后兼容，也可以是单个图片路径字符串
        enable_image: 是否启用图片
        pandoc_path: Pandoc可执行文件路径
        config: 配置对象(可选)
    """
    # 生成文件名（清理非法字符）
    safe_title = re.sub(r'[\\/*?:"<>|]', '', title)[:50]
    filename = f'{safe_title}.docx'

    # 从配置中获取输出目录，默认为 'output'
    if not config:
        config = load_config()
    output_dir = config.get('output_directory', 'output')
    os.makedirs(output_dir, exist_ok=True)

    filepath = os.path.join(output_dir, filename)

    # 处理图片插入
    if enable_image and image_list:
        # 兼容旧格式：如果是字符串路径，转为新格式
        if isinstance(image_list, str):
            if os.path.exists(image_list):
                # 单张图片，放在第一段后
                image_list = [{
                    'path': image_list,
                    'summary': '配图',
                    'paragraph_index': 0
                }]
            else:
                image_list = []

        # 使用新的多图插入方法
        if image_list:
            processed_content = inject_images_into_markdown(content, image_list)
        else:
            # 没有图片，添加提示
            processed_content = _add_no_image_warning(content)
    elif enable_image:
        # 启用图片但没有提供图片列表，添加提示
        processed_content = _add_no_image_warning(content)
    else:
        # 不启用图片
        processed_content = content

    # 保存 Markdown 文件
    md_filepath = filepath.replace('.docx', '.md')
    with open(md_filepath, 'w', encoding='utf-8') as f:
        f.write(processed_content)

    try:
        # 使用 pandoc 转换为 Word
        cmd = [
            pandoc_path,
            md_filepath,
            '-o', filepath,
            '--standalone'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            raise Exception(f'Pandoc 转换失败: {result.stderr}')

        # 删除临时 Markdown 文件
        try:
            os.remove(md_filepath)
        except:
            pass

        # 删除临时图片文件
        if image_list and isinstance(image_list, list):
            for img_info in image_list:
                img_path = img_info.get('path', '')
                if img_path and 'temp_' in os.path.basename(img_path) and os.path.exists(img_path):
                    try:
                        os.remove(img_path)
                    except:
                        pass

        return filename

    except FileNotFoundError:
        raise Exception(f'找不到 Pandoc，请检查路径配置: {pandoc_path}')
    except subprocess.TimeoutExpired:
        raise Exception('Pandoc 转换超时')
    except Exception as e:
        # 删除临时文件
        try:
            os.remove(md_filepath)
        except:
            pass
        raise e

def _add_no_image_warning(content):
    """在第一段后添加配图提示"""
    lines = content.split('\n')
    processed_content = []
    first_paragraph_found = False

    for line in lines:
        line_stripped = line.strip()
        processed_content.append(line)

        # 找到第一个普通段落（非标题、非空行）
        if not first_paragraph_found and line_stripped and not line_stripped.startswith('#'):
            first_paragraph_found = True
            # 在第一段后插入提示文字
            processed_content.append('')
            processed_content.append('**<span style="color:red;">请自行配图！！</span>**')
            processed_content.append('')

    return '\n'.join(processed_content)

@app.route('/api/generate/status/<task_id>', methods=['GET'])
def get_generation_status(task_id):
    """获取生成任务的状态"""
    with task_lock:
        task = generation_tasks.get(task_id)
        if not task:
            return jsonify({'error': '任务不存在'}), 404
        # 返回任务的副本以避免在迭代时被修改
        task_copy = task.copy()
        print(f"[API] 返回任务状态: results={len(task_copy['results'])}, errors={len(task_copy['errors'])}, status={task_copy['status']}")
        return jsonify(task_copy)

@app.route('/api/generate/retry', methods=['POST'])
def retry_failed_topics():
    """重试失败的主题"""
    data = request.json
    task_id = data.get('task_id')
    topics_to_retry = data.get('topics', [])

    if not task_id or not topics_to_retry:
        return jsonify({'error': '缺少 task_id 或 topics'}), 400

    with task_lock:
        task = generation_tasks.get(task_id)
        if not task:
            return jsonify({'error': '任务不存在'}), 404

        # 从错误列表中移除需要重试的主题
        new_errors = [e for e in task['errors'] if e['topic'] not in topics_to_retry]
        task['errors'] = new_errors

        # 更新任务状态，但保持总数不变
        task['status'] = 'running'

        # 根据原始总数重新计算进度
        completed_count = len(task['results']) + len(task['errors'])
        if task.get('total', 0) > 0:
            task['progress'] = (completed_count / task['total']) * 100
        else:
            task['progress'] = 0

    # 重新提交任务
    config = load_config()
    executor.submit(_execute_generation_task, task_id, topics_to_retry, config)

    return jsonify({'success': True, 'message': f'已重新提交 {len(topics_to_retry)} 个主题进行生成'})

@app.route('/api/download/<filename>')
def download_file(filename):
    """下载生成的文档"""
    config = load_config()
    output_dir = config.get('output_directory', 'output')
    filepath = os.path.join(output_dir, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({'error': '文件不存在'}), 404

@app.route('/api/history')
def get_history():
    """获取历史记录"""
    try:
        config = load_config()
        output_dir = config.get('output_directory', 'output')

        files = []
        if os.path.exists(output_dir):
            for filename in os.listdir(output_dir):
                if filename.endswith('.docx') and not filename.startswith('~'):
                    filepath = os.path.join(output_dir, filename)
                    stats = os.stat(filepath)
                    # 文件名不再带时间戳，直接显示完整文件名作为标题
                    title = filename.replace('.docx', '')
                    files.append({
                        'filename': filename,
                        'size': stats.st_size,
                        'created': datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                        'title': title
                    })

        # 按创建时间倒序排列
        files.sort(key=lambda x: x['created'], reverse=True)
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _strip_json_text(text):
    """去除 ```json 代码块等包装"""
    cleaned = text.strip()
    if cleaned.startswith('```'):
        cleaned = re.sub(r'^```[a-zA-Z]*\n', '', cleaned)
        cleaned = re.sub(r'\n```$', '', cleaned)
    return cleaned.strip()

def _parse_json_response(text):
    """尽量从模型响应中解析 JSON"""
    cleaned = _strip_json_text(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', cleaned, re.S)
        if match:
            snippet = match.group(0)
            try:
                return json.loads(snippet)
            except json.JSONDecodeError:
                pass
    raise ValueError('无法解析模型返回的 JSON')

def generate_visual_blueprint(topic, article, api_key, base_url, model_name):
    """调用 LLM 生成结构化的视觉描述"""
    if not api_key:
        return None

    truncated_article = article[:2000]
    prompt = f"""你是一名资深视觉导演，请阅读以下文章内容，并产出一个用于 Stable Diffusion / ComfyUI 的视觉计划。
标题：{topic}
正文片段：{truncated_article}

请严格按照以下 JSON 结构输出，所有字段必须使用英文短语，长度 4-15 个词：
{{
  "template": "portrait|urban_story|technology|nature|editorial|abstract",
  "subject": "...",
  "scene": "...",
  "mood": "...",
  "style": "...",
  "lighting": "...",
  "composition": "...",
  "details": "...",
  "negative": "..."
}}

要求：
1. template 字段只能取上述枚举之一。
2. 其它字段写出具体可视化描述，使用英文逗号分隔短语。
3. negative 字段写出不希望出现的画面元素，使用英文。
4. 只输出 JSON，禁止添加额外解释或 Markdown。
"""

    url = f'{base_url}/v1beta/models/{model_name}:generateContent?key={api_key}'
    headers = {'Content-Type': 'application/json'}
    data = {
        'contents': [{
            'parts': [{'text': prompt}]
        }]
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    result = response.json()
    if 'candidates' not in result or not result['candidates']:
        raise Exception('视觉描述生成失败：没有候选内容')

    raw_text = result['candidates'][0]['content']['parts'][0]['text']

    try:
        blueprint = _parse_json_response(raw_text)
    except ValueError as exc:
        raise Exception(f'视觉描述 JSON 解析失败: {exc}')

    template = blueprint.get('template', 'editorial')
    if template not in VISUAL_TEMPLATE_PRESETS:
        template = 'editorial'

    def _normalize_field(value, fallback):
        if not value:
            return fallback
        return str(value).strip()

    normalized = {
        'template': template,
        'subject': _normalize_field(blueprint.get('subject'), topic),
        'scene': _normalize_field(blueprint.get('scene'), f'story about {topic}'),
        'mood': _normalize_field(blueprint.get('mood'), 'dramatic and inspiring'),
        'style': _normalize_field(blueprint.get('style'), 'cinematic, highly detailed'),
        'lighting': _normalize_field(blueprint.get('lighting'), 'soft cinematic lighting'),
        'composition': _normalize_field(blueprint.get('composition'), 'balanced composition'),
        'details': _normalize_field(blueprint.get('details'), 'intricate storytelling details'),
        'negative': _normalize_field(blueprint.get('negative'), 'lowres, blurry, distorted, watermark')
    }

    return normalized

def build_visual_prompts(blueprint):
    """根据视觉蓝图和模板生成正/负向提示词"""
    if not blueprint:
        return None

    template_key = blueprint.get('template', 'editorial')
    preset = VISUAL_TEMPLATE_PRESETS.get(template_key, VISUAL_TEMPLATE_PRESETS['editorial'])

    parts = [
        preset['positive_prefix'],
        blueprint.get('subject', ''),
        blueprint.get('scene', ''),
        blueprint.get('composition', ''),
        blueprint.get('details', ''),
        blueprint.get('style', ''),
        blueprint.get('mood', ''),
        blueprint.get('lighting', '')
    ]

    positive_body = ', '.join(filter(None, [p.strip() for p in parts if p]))
    positive_prompt = f"{positive_body}, {preset['positive_suffix']}".strip(', ')

    negative_parts = [
        preset.get('negative', ''),
        blueprint.get('negative', '')
    ]
    negative_prompt = ', '.join(filter(None, [p.strip() for p in negative_parts if p]))

    return {
        'template': template_key,
        'positive_prompt': positive_prompt,
        'negative_prompt': negative_prompt or preset.get('negative', '')
    }



def apply_style_to_prompts(prompts, config):
    merged = dict(prompts) if prompts else {}
    template_id = config.get('comfyui_style_template', 'custom')
    template = IMAGE_STYLE_TEMPLATES.get(template_id, IMAGE_STYLE_TEMPLATES['custom'])

    if template_id == 'custom':
        style_positive = (config.get('comfyui_positive_style') or '').strip()
        style_negative = (config.get('comfyui_negative_style') or '').strip()
    else:
        style_positive = (template.get('positive', '') or '').strip()
        style_negative = (template.get('negative', '') or '').strip()
        extra_positive = (config.get('comfyui_positive_style') or '').strip()
        extra_negative = (config.get('comfyui_negative_style') or '').strip()
        if extra_positive:
            style_positive = f"{style_positive}, {extra_positive}" if style_positive else extra_positive
        if extra_negative:
            style_negative = f"{style_negative}, {extra_negative}" if style_negative else extra_negative

    def merge(style_text, original):
        original = (original or '').strip()
        if style_text:
            if original:
                return f"{original}, {style_text}"  # 原始内容在前，风格在后
            return style_text
        return original

    merged['positive_prompt'] = merge(style_positive, merged.get('positive_prompt'))
    merged['negative_prompt'] = merge(style_negative, merged.get('negative_prompt'))
    merged['style_template'] = template_id
    return merged

def derive_keyword_from_blueprint(blueprint):
    """从视觉蓝图中提取英文关键词，用于备用图片源"""
    if not blueprint:
        return ''
    text = ' '.join([
        str(blueprint.get('subject', '')),
        str(blueprint.get('scene', '')),
        str(blueprint.get('details', ''))
    ])
    words = re.findall(r'[A-Za-z]+', text)
    if not words:
        return ''
    return ' '.join(words[:4]).lower()

def extract_paragraph_structures(markdown_text):
    """从Markdown文章中提取段落结构"""
    lines = markdown_text.split('\n')
    paragraphs = []
    current_para = []
    start_line = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        # 跳过空行和标题行
        if not stripped or stripped.startswith('#'):
            if current_para:
                # 保存当前段落
                paragraphs.append({
                    'text': '\n'.join(current_para),
                    'start_line': start_line,
                    'end_line': i - 1
                })
                current_para = []
            continue

        # 开始新段落
        if not current_para:
            start_line = i
        current_para.append(line)

    # 保存最后一个段落
    if current_para:
        paragraphs.append({
            'text': '\n'.join(current_para),
            'start_line': start_line,
            'end_line': len(lines) - 1
        })

    return paragraphs

def compute_image_slots(paragraphs, target_count):
    """计算图片插入位置

    策略：
    - 避免图片放在文章最后一段之后
    - 尽量均匀分布
    - 段落不足时智能处理
    """
    if not paragraphs:
        return [None] * target_count

    para_count = len(paragraphs)

    if para_count == 1:
        # 只有1段，所有图片都放在这一段后
        return [0] * target_count

    if para_count == 2:
        # 只有2段的情况
        if target_count == 1:
            return [0]  # 放在第一段后
        elif target_count == 2:
            return [0, 1]  # 两段各放一张
        else:  # target_count == 3
            return [0, 0, 1]  # 第一段后放2张，第二段后放1张

    # 3段及以上的情况
    if para_count < target_count:
        # 段落不足，将多余的图片插入到倒数第二段
        # 例如：4张图片，3个段落 -> [0, 1, 1, 2] 而不是 [0, 1, 2, None]
        slots = list(range(para_count - 1))  # 先占满前 para_count-1 个位置
        remaining = target_count - (para_count - 1)
        # 剩余的图片分散在前面的段落，优先放在中间段落
        for i in range(remaining):
            insert_pos = min(para_count - 2, (para_count - 2) // 2)  # 倾向于放在中间偏前
            slots.append(insert_pos)
        return sorted(slots)

    # 段落足够，均匀分布
    if target_count == 1:
        # 单张图片放在第一段后
        return [0]
    elif target_count == 3:
        # 3张图片分别放在前、中、倒数第二段后
        # 确保最后一张不在文末（不能是 para_count - 1）
        if para_count == 3:
            # 特殊情况：3段3图，放在 [0, 1, 1]，最后两张都在第二段后
            return [0, 1, 1]
        else:
            # 4段及以上：均匀分布，但最后一张在倒数第二段
            middle = para_count // 2
            last_pos = para_count - 2  # 倒数第二段
            return [0, middle, last_pos]
    else:
        # 其他情况均匀分布，但最后一张不放在最后一段
        step = (para_count - 1) / target_count  # 注意：减1确保不会到最后一段
        return [min(int(i * step), para_count - 2) for i in range(target_count)]

def summarize_paragraph_for_image(paragraph_text, topic, config):
    """为段落生成图片摘要（英文视觉描述）"""
    summary_model = config.get('comfyui_summary_model', '__default__')

    # 如果选择默认模型，使用主写作模型
    if summary_model == '__default__':
        summary_model = config.get('default_model', 'gemini-pro')

    api_key = config.get('gemini_api_key', '')
    base_url = config.get('gemini_base_url', 'https://generativelanguage.googleapis.com')

    if not api_key:
        return f"visual representation of {topic}"

    # 限制段落长度
    truncated_para = paragraph_text[:500]

    prompt = f"""阅读以下关于「{topic}」的文章段落，为其生成适合图片生成的中文视觉描述。

要求：
1. 描述段落中的主要主体、动作或场景（15-30个汉字）
2. 要具体且可视化 - 描述你会看到什么，而不是抽象概念
3. 使用具体的名词、生动的动词和具体细节
4. 聚焦于视觉元素：物体、人物、地点、动作、氛围
5. 只输出中文描述，不要引号或额外文字

段落内容：
{truncated_para}

视觉描述："""

    try:
        url = f'{base_url}/v1beta/models/{summary_model}:generateContent?key={api_key}'
        headers = {'Content-Type': 'application/json'}
        data = {
            'contents': [{
                'parts': [{'text': prompt}]
            }]
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()

        result = response.json()
        if 'candidates' in result and len(result['candidates']) > 0:
            summary = result['candidates'][0]['content']['parts'][0]['text']
            summary = summary.strip().strip('"').strip("'")
            print(f"段落摘要生成成功: {summary}")
            return summary
        else:
            raise Exception('无法从API响应中提取摘要')
    except Exception as e:
        print(f"段落摘要生成失败: {e}，使用降级方案")
        # 降级：使用主题或段落前50字符
        fallback = paragraph_text[:50].strip()
        if fallback:
            return f"illustration of {fallback}"
        return f"visual representation of {topic}"

def inject_images_into_markdown(markdown_text, image_list):
    """将多张图片按指定位置插入到Markdown文章中

    Args:
        markdown_text: 原始Markdown文本
        image_list: 图片列表，每项包含 {'path', 'summary', 'paragraph_index'}
                   paragraph_index为None时表示放在文末
    Returns:
        处理后的Markdown文本
    """
    if not image_list:
        return markdown_text

    lines = markdown_text.split('\n')
    paragraphs = extract_paragraph_structures(markdown_text)

    # 为每个段落创建插入列表
    insertions = {}
    end_insertions = []

    for img_info in image_list:
        para_idx = img_info.get('paragraph_index')
        img_path = img_info.get('path', '')
        # 不在文章中显示详细描述，使用空的 alt 文本
        img_alt = ""

        if para_idx is None:
            # 文末插入
            end_insertions.append(f"![{img_alt}]({img_path})")
        elif 0 <= para_idx < len(paragraphs):
            # 在指定段落后插入
            para = paragraphs[para_idx]
            insert_line = para['end_line'] + 1
            if insert_line not in insertions:
                insertions[insert_line] = []
            insertions[insert_line].append(f"![{img_alt}]({img_path})")

    # 从后向前插入，避免索引变化
    for line_idx in sorted(insertions.keys(), reverse=True):
        insert_content = insertions[line_idx]
        # 每张图片前后加空行
        for img_md in reversed(insert_content):
            lines.insert(line_idx, '')
            lines.insert(line_idx, img_md)
            lines.insert(line_idx, '')

    # 文末插入
    if end_insertions:
        lines.append('')
        for img_md in end_insertions:
            lines.append('')
            lines.append(img_md)
            lines.append('')

    return '\n'.join(lines)

def load_comfyui_prompt_graph(settings):
    """根据配置加载 ComfyUI workflow"""
    workflow_path = settings.get('workflow_path')
    if not workflow_path:
        raise ValueError('未配置 ComfyUI workflow 文件路径')

    workflow_path = Path(workflow_path).expanduser()
    if not workflow_path.is_absolute():
        workflow_path = Path.cwd() / workflow_path
    if not workflow_path.exists():
        raise FileNotFoundError(f'ComfyUI workflow 文件不存在: {workflow_path}')

    with open(workflow_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    if isinstance(raw_data, dict) and 'prompt' in raw_data:
        prompt_graph = raw_data['prompt']
    elif isinstance(raw_data, dict):
        prompt_graph = raw_data
    else:
        raise ValueError('ComfyUI workflow JSON 结构不正确，应为 {node_id: {...}} 或包含 prompt 字段')

    if not isinstance(prompt_graph, dict):
        raise ValueError('ComfyUI prompt 应为字典结构')

    return copy.deepcopy(prompt_graph)


def build_comfyui_workflow_payload(prompts, settings):
    """根据模板工作流构造 ComfyUI API 所需的 payload"""
    prompt_graph = load_comfyui_prompt_graph(settings)

    seed = settings.get('seed', -1)
    if seed is None or seed < 0:
        seed = random.randint(1, 2**31 - 1)

    replacements = {
        '{{positive_prompt}}': prompts['positive_prompt'],
        '{{negative_prompt}}': prompts['negative_prompt'],
        '{{filename_prefix}}': 'auto_' + datetime.now().strftime('%Y%m%d')
    }

    for node in prompt_graph.values():
        inputs = node.get('inputs', {})
        if not isinstance(inputs, dict):
            continue

        for key, value in list(inputs.items()):
            if isinstance(value, str):
                for placeholder, actual in replacements.items():
                    if placeholder in value:
                        inputs[key] = value.replace(placeholder, actual)

            if key == 'seed':
                inputs[key] = seed
            elif key == 'filename_prefix' and isinstance(value, str) and '{{filename_prefix}}' not in value:
                inputs[key] = 'auto_' + datetime.now().strftime('%Y%m%d')

    return {
        'prompt': prompt_graph
    }
def submit_comfyui_prompt(payload, settings):
    server = settings.get('server_url', 'http://127.0.0.1:8188').rstrip('/')
    response = requests.post(f'{server}/prompt', json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    prompt_id = data.get('prompt_id')
    if not prompt_id:
        raise Exception('ComfyUI 未返回 prompt_id')
    return server, prompt_id

def poll_comfyui_history(server, prompt_id, settings):
    timeout = settings.get('timeout_seconds', 180)
    start = time.time()
    while time.time() - start < timeout:
        try:
            history_resp = requests.get(f'{server}/history/{prompt_id}', timeout=10)
            if history_resp.status_code == 404:
                time.sleep(2)
                continue
            history_resp.raise_for_status()
            history = history_resp.json() or {}

            prompt_data = None
            if isinstance(history, dict):
                if prompt_id in history and isinstance(history[prompt_id], dict):
                    prompt_data = history[prompt_id]
                else:
                    # history 可能只返回单个 prompt 数据
                    for value in history.values():
                        if isinstance(value, dict) and 'outputs' in value:
                            prompt_data = value
                            break
            if prompt_data is None and isinstance(history, dict):
                prompt_data = history

            if isinstance(prompt_data, dict):
                status_info = prompt_data.get('status') or {}
                status_value = status_info.get('status') if isinstance(status_info, dict) else None
                if status_value == 'error':
                    message = status_info.get('message') if isinstance(status_info, dict) else None
                    raise RuntimeError(message or 'ComfyUI 返回错误状态')

                outputs = prompt_data.get('outputs') or {}
                if outputs:
                    return outputs
                if status_value in ('completed', 'success'):
                    # 已完成但暂未拿到输出，稍后重试
                    time.sleep(1.5)
                    continue

        except requests.RequestException:
            pass
        time.sleep(2)
    raise TimeoutError('等待 ComfyUI 生成图片超时')

def download_comfyui_image(server, image_meta, output_dir, topic_slug, settings):
    filename = image_meta.get('filename')
    subfolder = image_meta.get('subfolder', '')
    image_type = image_meta.get('type', 'output')
    if not filename:
        return None

    params = {
        'filename': filename,
        'subfolder': subfolder,
        'type': image_type
    }
    view_resp = requests.get(f'{server}/view', params=params, timeout=30)
    view_resp.raise_for_status()

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    _, original_ext = os.path.splitext(filename)
    ext = settings.get('output_format') or original_ext.lstrip('.')
    if not ext:
        ext = 'png'
    ext = ext.replace('.', '')
    safe_topic = re.sub(r'[^a-zA-Z0-9_-]+', '_', topic_slug)[:40] or 'topic'
    local_filename = f'comfyui_{safe_topic}_{timestamp}.{ext}'
    local_path = os.path.join(output_dir, local_filename)

    with open(local_path, 'wb') as f:
        f.write(view_resp.content)

    return local_path

def generate_image_with_comfyui(topic, prompts, blueprint, config, settings_override=None, semaphore_override=None, test_mode=False):
    """调度 ComfyUI 自动生成图片"""
    if not prompts:
        return None, {}

    settings = settings_override or get_comfyui_settings(config)
    if not settings.get('enabled', True):
        return None, {}

    semaphore = semaphore_override or comfyui_runtime['semaphore']
    acquired = semaphore.acquire(timeout=settings.get('timeout_seconds', 180))
    if not acquired:
        print("ComfyUI 队列繁忙，放弃生成")
        return None, {}

    base_prompts = prompts or {}
    styled_prompts = apply_style_to_prompts(base_prompts, config)

    metadata = {
        'template': base_prompts.get('template'),
        'blueprint': blueprint,
        'positive_prompt': styled_prompts.get('positive_prompt'),
        'negative_prompt': styled_prompts.get('negative_prompt')
    }

    try:
        attempts = settings.get('max_attempts', 2)
        for attempt in range(1, attempts + 1):
            try:
                payload = build_comfyui_workflow_payload(styled_prompts, settings)
                server, prompt_id = submit_comfyui_prompt(payload, settings)
                outputs = poll_comfyui_history(server, prompt_id, settings)

                if isinstance(outputs, list):
                    outputs = {str(index): value for index, value in enumerate(outputs)}
                elif isinstance(outputs, str):
                    try:
                        parsed_outputs = json.loads(outputs)
                        if isinstance(parsed_outputs, dict):
                            outputs = parsed_outputs
                        elif isinstance(parsed_outputs, list):
                            outputs = {str(index): value for index, value in enumerate(parsed_outputs)}
                        else:
                            raise ValueError('Unsupported outputs structure')
                    except json.JSONDecodeError:
                        raise ValueError('ComfyUI 返回的 outputs 结构无法解析')
                elif not isinstance(outputs, dict):
                    raise ValueError('ComfyUI 返回的 outputs 结构不支持')

                image_path = None
                for node_output in outputs.values():
                    images = []
                    if isinstance(node_output, dict):
                        images = node_output.get('images') or []
                    elif isinstance(node_output, list):
                        images = node_output
                    elif isinstance(node_output, str):
                        try:
                            possible = json.loads(node_output)
                            if isinstance(possible, dict):
                                images = possible.get('images') or []
                            elif isinstance(possible, list):
                                images = possible
                        except json.JSONDecodeError:
                            images = []

                    for image_meta in images:
                        output_dir = os.path.join(config.get('output_directory', 'output'), 'comfyui_images')
                        image_path = download_comfyui_image(server, image_meta, output_dir, topic, settings)
                        if image_path:
                            metadata['comfyui'] = {
                                'prompt_id': prompt_id,
                                'node': image_meta.get('type'),
                                'filename': os.path.basename(image_path),
                                'attempt': attempt
                            }
                            return image_path, metadata

                raise Exception('未在 ComfyUI 输出中找到图片节点')

            except Exception as e:
                print(f"ComfyUI 生成失败（第 {attempt} 次）: {e}")
                metadata.setdefault('errors', []).append(str(e))
                time.sleep(3)

        return None, metadata

    finally:
        semaphore.release()

def find_available_port(start_port=5000, max_attempts=10):
    """查找可用端口，从start_port开始尝试"""
    import socket
    for port in range(start_port, start_port + max_attempts):
        try:
            # 尝试绑定端口
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('0.0.0.0', port))
            sock.close()
            return port
        except OSError:
            # 端口被占用，尝试下一个
            continue
    # 所有端口都被占用，返回None
    return None

if __name__ == '__main__':
    # 只在主进程中查找端口（避免debug模式重载器重复查找）
    import os
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # 这是主进程，查找可用端口
        port = find_available_port(5000)
        if port is None:
            print("错误: 无法找到可用端口 (5000-5009 都被占用)")
            exit(1)

        if port != 5000:
            print(f"提示: 端口 5000 被占用，使用端口 {port} 启动服务")

        print(f"应用启动在 http://localhost:{port}")
        # 将端口保存到环境变量，供重载器进程使用
        os.environ['APP_PORT'] = str(port)
    else:
        # 这是重载器进程，使用已找到的端口
        port = int(os.environ.get('APP_PORT', 5000))

    app.run(debug=True, host='0.0.0.0', port=port)
