"""配置管理 API 路由"""

from flask import Blueprint, request, jsonify
from app.config.loader import load_config, save_config, get_comfyui_settings, get_gemini_image_settings
from app.config import IMAGE_STYLE_TEMPLATES
from app.services import update_comfyui_runtime, get_available_models
from app.services.task_service import create_executor
from app.services.gemini_image_service import (
    test_gemini_image_api,
    get_gemini_image_models,
    GEMINI_IMAGE_STYLE_PRESETS
)

config_api_bp = Blueprint('config_api', __name__, url_prefix='/api')


@config_api_bp.route('/config', methods=['GET', 'POST'])
def handle_config():
    """处理配置的获取和保存"""
    if request.method == 'GET':
        config = load_config()
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
            # 摘要模型独立配置，向后兼容：如果是 __default__ 或未设置，使用主写作模型
            'comfyui_summary_model': config.get('comfyui_summary_model') if config.get('comfyui_summary_model') and config.get('comfyui_summary_model') != '__default__' else config.get('default_model', 'gemini-pro'),
            'comfyui_style_templates': [
                {'id': key, 'label': value['label']}
                for key, value in IMAGE_STYLE_TEMPLATES.items()
            ],
            'gemini_image_settings': get_gemini_image_settings(config),
            # 检查是否配置了独立的 Gemini 图像 API Key（不包括回退的主模型 API Key）
            'gemini_image_api_key_set': bool(config.get('gemini_image_settings', {}).get('api_key')),
            # 检查是否配置了独立的 Gemini 图像 Base URL（不包括回退的主模型 Base URL）
            'gemini_image_base_url_set': bool(config.get('gemini_image_settings', {}).get('base_url')),
            'gemini_image_style_presets': [
                {'id': key, 'name': value['name']}
                for key, value in GEMINI_IMAGE_STYLE_PRESETS.items()
            ]
        })

    elif request.method == 'POST':
        new_config = request.json
        old_config = load_config()

        # 合并配置
        final_config = {
            'gemini_base_url': new_config.get('gemini_base_url', 'https://generativelanguage.googleapis.com'),
            'pandoc_path': new_config.get('pandoc_path', ''),
            'default_model': new_config.get('default_model', 'gemini-pro'),
            'default_prompt': new_config.get('default_prompt', ''),
            'max_concurrent_tasks': int(new_config.get('max_concurrent_tasks', old_config.get('max_concurrent_tasks', 3))),
            'image_source_priority': new_config.get('image_source_priority', old_config.get('image_source_priority', [])),
            'local_image_directories': new_config.get('local_image_directories', old_config.get('local_image_directories', [])),
            'enable_user_upload': new_config.get('enable_user_upload', old_config.get('enable_user_upload', True)),
            'uploaded_images_dir': new_config.get('uploaded_images_dir', old_config.get('uploaded_images_dir', 'uploads')),
            'output_directory': new_config.get('output_directory', old_config.get('output_directory', 'output')),
            'comfyui_positive_style': new_config.get('comfyui_positive_style', old_config.get('comfyui_positive_style', '')),
            'comfyui_negative_style': new_config.get('comfyui_negative_style', old_config.get('comfyui_negative_style', '')),
            'comfyui_image_count': int(new_config.get('comfyui_image_count', old_config.get('comfyui_image_count', 1))),
            'comfyui_style_template': new_config.get('comfyui_style_template', old_config.get('comfyui_style_template', 'custom')),
            # 摘要模型独立配置，默认使用主写作模型
            'comfyui_summary_model': new_config.get('comfyui_summary_model', old_config.get('comfyui_summary_model', new_config.get('default_model', old_config.get('default_model', 'gemini-pro'))))
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

        # 处理 Gemini 图像生成配置
        gemini_image_settings_payload = new_config.get('gemini_image_settings', {})
        old_gemini_image_settings = old_config.get('gemini_image_settings', {})

        # 合并新旧配置，保留旧的 API Key 和 Base URL（如果新配置中没有提供）
        merged_gemini_image_settings = {**old_gemini_image_settings, **gemini_image_settings_payload}

        # 特殊处理 API Key：只有在新配置中明确提供了才覆盖，否则保留旧值
        if 'api_key' not in gemini_image_settings_payload and 'api_key' in old_gemini_image_settings:
            merged_gemini_image_settings['api_key'] = old_gemini_image_settings['api_key']

        # 特殊处理 Base URL：只有在新配置中明确提供了才覆盖，否则保留旧值
        if 'base_url' not in gemini_image_settings_payload and 'base_url' in old_gemini_image_settings:
            merged_gemini_image_settings['base_url'] = old_gemini_image_settings['base_url']

        final_config['gemini_image_settings'] = merged_gemini_image_settings

        if final_config['comfyui_image_count'] not in (1, 3):
            final_config['comfyui_image_count'] = 1

        if final_config['comfyui_style_template'] not in IMAGE_STYLE_TEMPLATES:
            final_config['comfyui_style_template'] = 'custom'

        # 摘要模型验证：如果未设置，使用主写作模型
        if not final_config['comfyui_summary_model'] or final_config['comfyui_summary_model'] == '__default__':
            final_config['comfyui_summary_model'] = final_config.get('default_model', 'gemini-pro')

        save_config(final_config)
        create_executor(final_config.get('max_concurrent_tasks', 3))
        update_comfyui_runtime(final_config)

        return jsonify({'success': True, 'message': '配置保存成功'})


@config_api_bp.route('/models')
def get_models():
    """获取可用的 Gemini 模型列表（支持缓存）"""
    from app.utils.models_cache import get_gemini_models_cache, update_gemini_models_cache

    # 检查是否强制刷新
    force_refresh = request.args.get('refresh', 'false').lower() == 'true'

    # 如果不是强制刷新，先尝试从缓存读取
    if not force_refresh:
        cache_data = get_gemini_models_cache()
        if cache_data['models']:
            print(f"✓ 从缓存加载 Gemini 主模型列表 (上次更新: {cache_data['last_updated']})")
            return jsonify({
                'models': cache_data['models'],
                'from_cache': True,
                'last_updated': cache_data['last_updated']
            })

    # 从 API 获取最新的模型列表
    config = load_config()
    api_key = config.get('gemini_api_key', '')
    base_url = config.get('gemini_base_url', 'https://generativelanguage.googleapis.com')

    if not api_key:
        return jsonify({'error': '请先配置 Gemini API Key'}), 400

    try:
        print(f"🔄 从 API 获取 Gemini 主模型列表...")
        model_list = get_available_models(api_key, base_url)

        # 更新缓存
        update_gemini_models_cache(model_list)
        print(f"✓ Gemini 主模型列表已缓存 ({len(model_list)} 个模型)")

        return jsonify({
            'models': model_list,
            'from_cache': False
        })
    except Exception as e:
        return jsonify({'error': f'获取模型列表失败: {str(e)}'}), 500


@config_api_bp.route('/check-pandoc', methods=['GET'])
def check_pandoc():
    """检查 Pandoc 配置状态"""
    config = load_config()
    pandoc_path = config.get('pandoc_path', '')
    return jsonify({
        'pandoc_configured': bool(pandoc_path),
        'pandoc_path': pandoc_path if pandoc_path else None
    })


@config_api_bp.route('/gemini-image-models', methods=['GET'])
def get_gemini_image_model_list():
    """获取 Gemini 图像生成模型列表（支持缓存）"""
    from app.utils.models_cache import get_gemini_image_models_cache, update_gemini_image_models_cache

    # 检查是否强制刷新
    force_refresh = request.args.get('refresh', 'false').lower() == 'true'

    # 如果不是强制刷新，先尝试从缓存读取
    if not force_refresh:
        cache_data = get_gemini_image_models_cache()
        if cache_data['models']:
            print(f"✓ 从缓存加载 Gemini 图像模型列表 (上次更新: {cache_data['last_updated']})")
            return jsonify({
                'success': True,
                'models': cache_data['models'],
                'from_cache': True,
                'last_updated': cache_data['last_updated']
            })

    # 从 API 获取最新的模型列表
    config = load_config()
    gemini_image_settings = get_gemini_image_settings(config)

    # 优先使用 Gemini 图像专用的 API key 和 base URL
    api_key = gemini_image_settings.get('api_key')
    base_url = gemini_image_settings.get('base_url')

    # 如果没有配置，返回提示
    if not api_key or not base_url:
        return jsonify({
            'success': False,
            'error': '请先配置 Gemini 图像生成的 API Key 和 Base URL',
            'models': []
        })

    try:
        print(f"🔄 从 API 获取 Gemini 图像模型列表...")
        models = get_gemini_image_models(api_key, base_url)

        # 更新缓存
        update_gemini_image_models_cache(models)
        print(f"✓ Gemini 图像模型列表已缓存 ({len(models)} 个模型)")

        return jsonify({
            'success': True,
            'models': models,
            'from_cache': False
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取模型列表失败: {str(e)}',
            'models': []
        })


@config_api_bp.route('/test-gemini-image', methods=['POST'])
def test_gemini_image():
    """测试 Gemini 图像生成 API"""
    data = request.json
    api_key = data.get('api_key')
    base_url = data.get('base_url')
    model = data.get('model', 'imagen-3.0-generate-001')

    # 如果没有提供配置，尝试从已保存的配置中读取
    config = load_config()
    gemini_image_settings = get_gemini_image_settings(config)

    if not api_key:
        # 尝试使用 Gemini 图像专用的 API key，如果没有则使用通用的
        api_key = gemini_image_settings.get('api_key')
        if not api_key:
            return jsonify({'success': False, 'message': '请先配置 Gemini API Key'})

    if not base_url:
        # 尝试使用 Gemini 图像专用的 Base URL，如果没有则使用通用的
        base_url = gemini_image_settings.get('base_url')
        if not base_url:
            base_url = 'https://generativelanguage.googleapis.com'

    try:
        success, message, image_path = test_gemini_image_api(api_key, base_url, model)

        if success:
            return jsonify({
                'success': True,
                'message': message,
                'image_path': image_path
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'测试失败: {str(e)}'
        })


@config_api_bp.route('/gemini-image-styles', methods=['GET'])
def get_gemini_image_style_list():
    """获取 Gemini 图像生成风格预设列表"""
    styles = [
        {'id': key, 'name': value['name']}
        for key, value in GEMINI_IMAGE_STYLE_PRESETS.items()
    ]
    return jsonify({'styles': styles})
