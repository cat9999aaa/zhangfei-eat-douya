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
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

app = Flask(__name__)
CORS(app)

# 全局任务存储和线程锁
generation_tasks = {}
task_lock = threading.Lock()

# 确保基础目录存在（output目录会在配置加载后根据配置创建）
os.makedirs('uploads', exist_ok=True)

# 允许的图片文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}

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
            'image_source_priority': config.get('image_source_priority', ['unsplash', 'pexels', 'pixabay', 'local']),
            'local_image_directories': config.get('local_image_directories', [{'path': 'pic', 'tags': ['default']}]),
            'enable_user_upload': config.get('enable_user_upload', True),
            'uploaded_images_dir': config.get('uploaded_images_dir', 'uploads'),
            'output_directory': config.get('output_directory', 'output')
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
            'image_source_priority': new_config.get('image_source_priority', old_config.get('image_source_priority', ['unsplash', 'pexels', 'pixabay', 'local'])),
            'local_image_directories': new_config.get('local_image_directories', old_config.get('local_image_directories', [{'path': 'pic', 'tags': ['default']}])),
            'enable_user_upload': new_config.get('enable_user_upload', old_config.get('enable_user_upload', True)),
            'uploaded_images_dir': new_config.get('uploaded_images_dir', old_config.get('uploaded_images_dir', 'uploads')),
            'output_directory': new_config.get('output_directory', old_config.get('output_directory', 'output'))
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

        save_config(final_config)
        # 更新线程池大小
        create_executor(final_config.get('max_concurrent_tasks', 3))
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

def get_image_with_priority(keyword, config, user_uploaded_path=None):
    """根据优先级策略获取图片"""
    # 用户自定义图片具有最高优先级，直接返回
    if user_uploaded_path and os.path.exists(user_uploaded_path):
        print(f"✓ 使用用户自定义图片: {user_uploaded_path}")
        return user_uploaded_path

    priority = config.get('image_source_priority', ['unsplash', 'pexels', 'pixabay', 'local', 'user_uploaded'])

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

def _execute_single_article_generation(topic, config, user_uploaded_image=None):
    """为单个主题生成文章（将在后台线程中执行）"""
    gemini_api_key = config.get('gemini_api_key', '')
    gemini_base_url = config.get('gemini_base_url', 'https://generativelanguage.googleapis.com')
    pandoc_path = config.get('pandoc_path', '')
    model_name = config.get('default_model') or 'gemini-pro'
    custom_prompt = config.get('default_prompt', '')
    enable_image = config.get('enable_image', True)

    # 1. 使用 Gemini 生成文章
    article = generate_article_with_gemini(topic, gemini_api_key, gemini_base_url, model_name, custom_prompt)
    article_title = extract_article_title(article)

    # 2. 提取关键词并获取图片（使用优先级策略）
    image_path = None
    image_keyword = ''
    image_source = 'none'

    if enable_image:
        # 提取关键词
        image_keyword = extract_image_keyword(article, gemini_api_key, gemini_base_url, model_name)

        # 使用优先级策略获取图片
        image_path = get_image_with_priority(image_keyword, config, user_uploaded_image)

        if image_path:
            # 判断图片来源
            if user_uploaded_image and image_path == user_uploaded_image:
                image_source = 'user_uploaded'
            elif 'temp_' in os.path.basename(image_path):
                image_source = 'api'  # Unsplash/Pexels/Pixabay
            else:
                image_source = 'local'

    # 3. 生成 Word 文档
    filename = create_word_document(article_title, article, image_path, enable_image, pandoc_path)

    return {
        'success': True,
        'topic': topic,
        'article_title': article_title,
        'filename': filename,
        'image_keyword': image_keyword,
        'has_image': image_path is not None,
        'image_source': image_source
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
            # 获取该主题对应的图片信息
            topic_image_info = topic_images.get(topic)
            user_image_path = None

            if topic_image_info:
                if topic_image_info.get('type') == 'uploaded':
                    user_image_path = topic_image_info.get('path')
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
                        user_image_path = temp_path
                    except Exception as e:
                        print(f"下载URL图片失败 ({topic}): {e}")

            futures[single_task_executor.submit(_execute_single_article_generation, topic, config, user_image_path)] = topic

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

def create_word_document(title, content, image_path=None, enable_image=True, pandoc_path='pandoc'):
    """使用 pandoc 将 Markdown 转换为 Word 文档"""

    # 生成文件名（清理非法字符）
    safe_title = re.sub(r'[\\/*?:"<>|]', '', title)[:50]
    filename = f'{safe_title}.docx'

    # 从配置中获取输出目录，默认为 'output'
    config = load_config()
    output_dir = config.get('output_directory', 'output')
    os.makedirs(output_dir, exist_ok=True)

    filepath = os.path.join(output_dir, filename)

    # 处理内容：在第一段后插入图片标记
    lines = content.split('\n')
    processed_content = []
    first_paragraph_found = False

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        processed_content.append(line)

        # 找到第一个普通段落（非标题、非空行）
        if not first_paragraph_found and line_stripped and not line_stripped.startswith('#'):
            first_paragraph_found = True

            # 在第一段后插入图片或提示
            if enable_image:
                if image_path and os.path.exists(image_path):
                    # 插入图片标记
                    processed_content.append('')
                    processed_content.append(f'![配图]({image_path})')
                    processed_content.append('')
                else:
                    # 插入提示文字
                    processed_content.append('')
                    processed_content.append('**<span style="color:red;">请自行配图！！</span>**')
                    processed_content.append('')

    # 保存 Markdown 文件
    md_filepath = filepath.replace('.docx', '.md')
    with open(md_filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(processed_content))

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

        # 仅当图片是临时文件时才删除
        if image_path and 'temp_' in os.path.basename(image_path) and os.path.exists(image_path):
            try:
                os.remove(image_path)
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
