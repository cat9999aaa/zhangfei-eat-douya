"""主要API路由（图片、生成、历史记录等）"""

import os
from flask import Blueprint, request, jsonify, send_file
from datetime import datetime
from werkzeug.utils import secure_filename

from app.config.loader import load_config
from app.config import ALLOWED_EXTENSIONS
from app.utils.file_helpers import allowed_file, generate_safe_filename
from app.utils.network import download_image_from_url as util_download_image
from app.services import (
    test_unsplash_connection,
    test_pexels_connection,
    test_pixabay_connection,
    test_comfyui_workflow,
    test_gemini_model,
    list_local_images,
    list_uploaded_images,
    list_generated_documents,
    create_generation_task,
    get_task_status,
    retry_failed_topics_in_task
)

main_api_bp = Blueprint('main_api', __name__, url_prefix='/api')


# ====================
# 图片相关 API
# ====================

@main_api_bp.route('/upload-image', methods=['POST'])
def upload_image():
    """用户上传图片"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': '未选择文件'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'success': False, 'error': '未选择文件'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': '不支持的文件格式'}), 400

    try:
        safe_filename = generate_safe_filename(file.filename, prefix='image_')
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


@main_api_bp.route('/list-local-images', methods=['GET'])
def list_local_images_endpoint():
    """列出本地图库中的所有图片"""
    try:
        config = load_config()
        images = list_local_images(config)
        return jsonify({'success': True, 'images': images, 'total': len(images)})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取图片列表失败: {str(e)}'}), 500


@main_api_bp.route('/list-uploaded-images', methods=['GET'])
def list_uploaded_images_endpoint():
    """列出用户上传的所有图片"""
    try:
        config = load_config()
        images = list_uploaded_images(config)
        return jsonify({'success': True, 'images': images, 'total': len(images)})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取上传图片列表失败: {str(e)}'}), 500


@main_api_bp.route('/download-image-from-url', methods=['POST'])
def download_image_from_url():
    """从URL下载图片到服务器"""
    data = request.json
    url = data.get('url', '')

    if not url:
        return jsonify({'success': False, 'error': '请提供图片URL'}), 400

    try:
        config = load_config()
        upload_dir = config.get('uploaded_images_dir', 'uploads')
        filepath = util_download_image(url, upload_dir)

        return jsonify({
            'success': True,
            'filename': os.path.basename(filepath),
            'path': filepath,
            'message': '图片下载成功'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f'下载失败: {str(e)}'}), 500


# ====================
# 生成相关 API
# ====================

@main_api_bp.route('/generate', methods=['POST'])
def generate_article():
    """启动文章生成任务"""
    data = request.json
    topics = data.get('topics', [])
    topic_images = data.get('topic_images', {})

    if not topics:
        return jsonify({'error': '请提供至少一个主题'}), 400

    config = load_config()
    if not config.get('gemini_api_key'):
        return jsonify({'error': '请先配置 Gemini API Key'}), 400
    if not config.get('pandoc_path'):
        return jsonify({'error': '请先在配置页面设置 Pandoc 可执行文件路径！'}), 400

    task_id = create_generation_task(topics, topic_images, config)
    return jsonify({'success': True, 'task_id': task_id})


@main_api_bp.route('/generate/status/<task_id>', methods=['GET'])
def get_generation_status(task_id):
    """获取生成任务的状态"""
    task = get_task_status(task_id)
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    return jsonify(task)


@main_api_bp.route('/generate/retry', methods=['POST'])
def retry_failed_topics():
    """重试失败的主题"""
    data = request.json
    task_id = data.get('task_id')
    topics_to_retry = data.get('topics', [])

    if not task_id or not topics_to_retry:
        return jsonify({'error': '缺少 task_id 或 topics'}), 400

    config = load_config()
    success = retry_failed_topics_in_task(task_id, topics_to_retry, config)

    if not success:
        return jsonify({'error': '任务不存在'}), 404

    return jsonify({'success': True, 'message': f'已重新提交 {len(topics_to_retry)} 个主题进行生成'})


# ====================
# 历史记录 API
# ====================

@main_api_bp.route('/history')
def get_history():
    """获取历史记录"""
    try:
        config = load_config()
        files = list_generated_documents(config)
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_api_bp.route('/download/<filename>')
def download_file(filename):
    """下载生成的文档"""
    config = load_config()
    output_dir = config.get('output_directory', 'output')
    filepath = os.path.join(output_dir, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({'error': '文件不存在'}), 404


# ====================
# 测试/健康检查 API
# ====================

@main_api_bp.route('/test-unsplash', methods=['POST'])
def test_unsplash():
    """测试 Unsplash API 配置"""
    data = request.json
    access_key = data.get('access_key', '').strip()

    # 如果没有提供 access_key，尝试使用已保存的配置
    if not access_key:
        config = load_config()
        access_key = config.get('unsplash_access_key', '')

    if not access_key:
        return jsonify({'success': False, 'error': '请提供 Access Key 或先保存配置'}), 400

    success, message, image_url = test_unsplash_connection(access_key)
    if success:
        return jsonify({'success': True, 'image_url': image_url, 'message': message})
    else:
        return jsonify({'success': False, 'error': message})


@main_api_bp.route('/test-pexels', methods=['POST'])
def test_pexels():
    """测试 Pexels API 配置"""
    data = request.json
    api_key = data.get('api_key', '').strip()

    # 如果没有提供 api_key，尝试使用已保存的配置
    if not api_key:
        config = load_config()
        api_key = config.get('pexels_api_key', '')

    if not api_key:
        return jsonify({'success': False, 'error': '请提供 API Key 或先保存配置'}), 400

    success, message, image_url = test_pexels_connection(api_key)
    if success:
        return jsonify({'success': True, 'image_url': image_url, 'message': message})
    else:
        return jsonify({'success': False, 'error': message})


@main_api_bp.route('/test-pixabay', methods=['POST'])
def test_pixabay():
    """测试 Pixabay API 配置"""
    data = request.json
    api_key = data.get('api_key', '').strip()

    # 如果没有提供 api_key，尝试使用已保存的配置
    if not api_key:
        config = load_config()
        api_key = config.get('pixabay_api_key', '')

    if not api_key:
        return jsonify({'success': False, 'error': '请提供 API Key 或先保存配置'}), 400

    success, message, image_url = test_pixabay_connection(api_key)
    if success:
        return jsonify({'success': True, 'image_url': image_url, 'message': message})
    else:
        return jsonify({'success': False, 'error': message})


@main_api_bp.route('/test-comfyui', methods=['POST'])
def test_comfyui():
    """测试 ComfyUI Workflow 配置"""
    data = request.json or {}
    try:
        config = load_config()
        prompts = {
            'template': 'test',
            'positive_prompt': data.get('positive_prompt', 'cinematic concept art, ultra detailed'),
            'negative_prompt': data.get('negative_prompt', 'lowres, blurry, watermark')
        }

        from app.config.loader import get_comfyui_settings
        settings = get_comfyui_settings(config)
        if data.get('comfyui_settings'):
            settings.update(data['comfyui_settings'])

        temp_config = dict(config)
        temp_config['comfyui_settings'] = settings
        if 'comfyui_positive_style' in data:
            temp_config['comfyui_positive_style'] = data['comfyui_positive_style']
        if 'comfyui_negative_style' in data:
            temp_config['comfyui_negative_style'] = data['comfyui_negative_style']

        success, message, result = test_comfyui_workflow(prompts, temp_config, settings)

        if success:
            return jsonify({'success': True, 'image_path': result['image_path'], 'metadata': result['metadata']})
        else:
            return jsonify({'success': False, 'error': message})

    except Exception as e:
        return jsonify({'success': False, 'error': f'测试失败: {str(e)}'}), 500


@main_api_bp.route('/test-model', methods=['POST'])
def test_model():
    """测试 Gemini 模型"""
    data = request.json
    model_name = data.get('model_name', '')
    api_key = data.get('api_key', '')
    base_url = data.get('base_url', 'https://generativelanguage.googleapis.com')

    if not model_name:
        return jsonify({'success': False, 'error': '请提供模型名称'}), 400

    if not api_key:
        config = load_config()
        api_key = config.get('gemini_api_key', '')
        if not api_key:
            return jsonify({'success': False, 'error': '请先配置 Gemini API Key'}), 400

    try:
        success, result = test_gemini_model(model_name, api_key, base_url)
        if success:
            return jsonify({'success': True, 'message': '模型测试成功', 'reply': result})
        else:
            return jsonify({'success': False, 'error': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'测试失败: {str(e)}'}), 500
