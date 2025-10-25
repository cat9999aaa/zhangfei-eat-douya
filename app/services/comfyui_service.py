"""ComfyUI 图片生成服务模块"""

import os
import re
import json
import copy
import time
import random
import threading
import requests
from datetime import datetime
from pathlib import Path
from app.config import IMAGE_STYLE_TEMPLATES, DEFAULT_COMFYUI_CONFIG
from app.config.loader import get_comfyui_settings


# ComfyUI 并发控制
comfyui_lock = threading.Lock()

# ComfyUI 运行时配置
comfyui_runtime = {
    'semaphore': threading.BoundedSemaphore(DEFAULT_COMFYUI_CONFIG['queue_size']),
    'queue_size': DEFAULT_COMFYUI_CONFIG['queue_size'],
    'config': DEFAULT_COMFYUI_CONFIG.copy()
}


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
        raise ValueError('ComfyUI workflow JSON 结构不正确')

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
    """提交 prompt 到 ComfyUI 服务器"""
    server = settings.get('server_url', 'http://127.0.0.1:8188').rstrip('/')
    response = requests.post(f'{server}/prompt', json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    prompt_id = data.get('prompt_id')
    if not prompt_id:
        raise Exception('ComfyUI 未返回 prompt_id')
    return server, prompt_id


def poll_comfyui_history(server, prompt_id, settings):
    """轮询 ComfyUI 历史记录，等待任务完成"""
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
                    time.sleep(1.5)
                    continue

        except requests.RequestException:
            pass
        time.sleep(2)

    raise TimeoutError('等待 ComfyUI 生成图片超时')


def download_comfyui_image(server, image_meta, output_dir, topic_slug, settings):
    """从 ComfyUI 服务器下载生成的图片"""
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


def apply_style_to_prompts(prompts, config):
    """应用风格模板到prompts"""
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
        """合并风格和原始提示词，风格在前，原始内容在后"""
        original = (original or '').strip()
        style_text = (style_text or '').strip()
        if style_text and original:
            # 风格提示词在前，摘要内容在后
            return f"{style_text}, {original}"
        return style_text or original

    merged['positive_prompt'] = merge(style_positive, merged.get('positive_prompt'))
    merged['negative_prompt'] = merge(style_negative, merged.get('negative_prompt'))
    merged['style_template'] = template_id
    return merged


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

                # 处理outputs结构
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

                # 查找并下载图片
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


def test_comfyui_workflow(prompts, config, settings_override=None):
    """测试 ComfyUI Workflow 配置"""
    try:
        if settings_override:
            settings = settings_override
        else:
            settings = get_comfyui_settings(config)

        if not settings.get('enabled', True):
            return False, '请先启用 ComfyUI 自动生成', None

        image_path, metadata = generate_image_with_comfyui(
            topic='comfyui_test',
            prompts=prompts,
            blueprint=None,
            config=config,
            settings_override=settings,
            test_mode=True
        )

        if image_path:
            return True, '测试成功', {'image_path': image_path, 'metadata': metadata}

        error_message = '生成失败'
        if metadata.get('errors'):
            error_message = metadata['errors'][-1]

        return False, error_message, metadata

    except Exception as e:
        return False, f'测试失败: {str(e)}', None
