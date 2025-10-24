"""任务管理服务模块"""

import threading
import requests
import os
import uuid
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.config import ALLOWED_EXTENSIONS
from app.config.loader import load_config
from app.utils.parsers import extract_article_title, derive_keyword_from_blueprint
from app.services.gemini_service import generate_article_with_gemini, generate_visual_blueprint, build_visual_prompts, summarize_paragraph_for_image
from app.services.document_service import extract_paragraph_structures, compute_image_slots, create_word_document
from app.services.comfyui_service import generate_image_with_comfyui

# 全局任务存储和线程锁
generation_tasks = {}
task_lock = threading.Lock()

# 线程池
executor = None


def create_executor(max_workers=3):
    """创建或更新线程池"""
    global executor
    if executor:
        executor.shutdown(wait=False)
    executor = ThreadPoolExecutor(max_workers=max_workers)
    return executor


def initialize_executor(config):
    """根据配置初始化线程池"""
    initial_workers = config.get('max_concurrent_tasks', 3)
    return create_executor(initial_workers)


def resolve_image_with_priority(keyword, config, user_uploaded_path=None, visual_prompts=None, blueprint=None, topic=None):
    """扩展版的图片获取逻辑，支持 ComfyUI 和 Gemini 图像生成并返回元数据"""
    from app.services.image_service import download_unsplash_image, download_pexels_image, download_pixabay_image, get_local_image_by_tags
    from app.services.gemini_image_service import generate_image_with_gemini
    from app.config.loader import get_comfyui_settings, get_gemini_image_settings

    comfy_settings = get_comfyui_settings(config)
    gemini_image_settings = get_gemini_image_settings(config)

    if user_uploaded_path and os.path.exists(user_uploaded_path):
        print(f"✓ 使用用户自定义图片: {user_uploaded_path}")
        return user_uploaded_path, 'user_uploaded', {}

    default_priority = ['gemini_image', 'comfyui', 'user_uploaded', 'pexels', 'unsplash', 'pixabay', 'local']
    priority = config.get('image_source_priority', default_priority)

    # 确保启用的生成源在优先级列表中
    if comfy_settings.get('enabled', True) and 'comfyui' not in priority:
        priority = ['comfyui'] + [src for src in priority if src != 'comfyui']

    if gemini_image_settings.get('enabled', True) and 'gemini_image' not in priority:
        priority = ['gemini_image'] + [src for src in priority if src != 'gemini_image']

    tags = keyword.lower().split() if keyword else []

    for source in priority:
        try:
            if source == 'gemini_image':
                # Gemini 图像生成
                if gemini_image_settings.get('enabled', True):
                    api_key = gemini_image_settings.get('api_key')
                    base_url = gemini_image_settings.get('base_url')
                    model = gemini_image_settings.get('model', 'imagen-3.0-generate-001')

                    if not api_key:
                        print("Gemini 图像生成未配置 API Key，跳过")
                        continue

                    # 构建提示词
                    if visual_prompts and visual_prompts.get('positive_prompt'):
                        prompt = visual_prompts['positive_prompt']
                    elif keyword:
                        prompt = keyword
                    else:
                        prompt = topic if topic else "beautiful image"

                    print(f"尝试使用 Gemini 生成图片，提示词: {prompt[:50]}...")

                    image_path, metadata = generate_image_with_gemini(
                        prompt=prompt,
                        api_key=api_key,
                        base_url=base_url,
                        model=model,
                        style=gemini_image_settings.get('style', 'realistic'),
                        aspect_ratio=gemini_image_settings.get('aspect_ratio', '16:9'),
                        custom_style_prefix=gemini_image_settings.get('custom_prefix', ''),
                        custom_style_suffix=gemini_image_settings.get('custom_suffix', ''),
                        max_retries=gemini_image_settings.get('max_retries', 3),
                        timeout=gemini_image_settings.get('timeout', 30)
                    )

                    if image_path:
                        print(f"Gemini 图像生成成功: {image_path}")
                        return image_path, 'gemini_image', metadata
                else:
                    print("Gemini 图像生成未启用，跳过")

            elif source == 'comfyui':
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


def execute_single_article_generation(topic, config, user_uploaded_images=None):
    """为单个主题生成文章（在后台线程中执行）"""
    gemini_api_key = config.get('gemini_api_key', '')
    gemini_base_url = config.get('gemini_base_url', 'https://generativelanguage.googleapis.com')
    pandoc_path = config.get('pandoc_path', '')
    model_name = config.get('default_model') or 'gemini-pro'
    custom_prompt = config.get('default_prompt', '')
    enable_image = config.get('enable_image', True)
    target_image_count = config.get('comfyui_image_count', 1)

    # 兼容旧格式
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
        user_image_count = len(user_uploaded_images) if user_uploaded_images else 0
        need_generate_count = target_image_count - user_image_count

        print(f"📊 图片配置: 目标数量={target_image_count}, 用户上传={user_image_count}, 需要生成={need_generate_count}")

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
                print(f"✓ 使用用户上传图片 {i+1}/{user_image_count}: {user_img.get('path')}")

        # 如果还需要更多图片，自动生成
        if need_generate_count > 0:
            print(f"🎨 需要生成 {need_generate_count} 张图片，调用摘要模型生成提示词...")
            try:
                visual_blueprint = generate_visual_blueprint(topic, article, gemini_api_key, gemini_base_url, model_name)
                visual_prompts = build_visual_prompts(visual_blueprint)
                image_keyword = derive_keyword_from_blueprint(visual_blueprint)
            except Exception as e:
                print(f"生成视觉蓝图失败: {e}")
                visual_blueprint = None
                visual_prompts = None
                image_keyword = ''

            for i in range(user_image_count, target_image_count):
                try:
                    slot_index = image_slots[i] if i < len(image_slots) else None

                    if slot_index is not None and slot_index < len(paragraphs):
                        para_text = paragraphs[slot_index]['text']
                        para_summary = summarize_paragraph_for_image(para_text, topic, config)
                    else:
                        para_summary = f"visual representation of {topic}"

                    if visual_prompts:
                        custom_prompts = {
                            'positive_prompt': para_summary,
                            'negative_prompt': visual_prompts.get('negative_prompt', 'lowres, blurry, watermark')
                        }
                    else:
                        custom_prompts = {
                            'positive_prompt': para_summary,
                            'negative_prompt': 'lowres, blurry, watermark'
                        }

                    image_path, image_source, image_metadata = resolve_image_with_priority(
                        image_keyword,
                        config,
                        None,
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
                        print(f"✗ 第 {i+1} 张图片生成失败，跳过")
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

    # 5. 生成 Word 文档
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


def execute_generation_task(task_id, topics, config):
    """后台任务执行函数 - 并行处理"""
    with task_lock:
        task = generation_tasks.get(task_id, {})
        topic_images = task.get('topic_images', {})

    with ThreadPoolExecutor(max_workers=config.get('max_concurrent_tasks', 3)) as single_task_executor:
        futures = {}
        for topic in topics:
            topic_image_info = topic_images.get(topic)
            user_uploaded_images = []

            if topic_image_info:
                if isinstance(topic_image_info, dict):
                    if topic_image_info.get('type') == 'uploaded':
                        user_uploaded_images.append({
                            'type': 'uploaded',
                            'path': topic_image_info.get('path'),
                            'summary': topic_image_info.get('summary', '配图'),
                            'order': 0
                        })
                    elif topic_image_info.get('type') == 'url':
                        url = topic_image_info.get('url')
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
                                'summary': topic_image_info.get('summary', '配图'),
                                'order': 0
                            })
                        except Exception as e:
                            print(f"下载URL图片失败 ({topic}): {e}")

                elif isinstance(topic_image_info, list):
                    for idx, img in enumerate(topic_image_info):
                        if img.get('type') == 'uploaded':
                            user_uploaded_images.append({
                                'type': 'uploaded',
                                'path': img.get('path'),
                                'summary': img.get('summary', '配图'),
                                'order': img.get('order', idx)
                            })
                        elif img.get('type') == 'url':
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

            futures[single_task_executor.submit(execute_single_article_generation, topic, config, user_uploaded_images)] = topic

        for future in as_completed(futures):
            topic = futures[future]
            try:
                result = future.result()
                with task_lock:
                    task = generation_tasks[task_id]
                    task['results'].append(result)
                    print(f"✓ 文章生成成功: {topic}")

            except Exception as e:
                with task_lock:
                    task = generation_tasks[task_id]
                    task['errors'].append({'topic': topic, 'error': str(e)})
                    print(f"✗ 文章生成失败: {topic} - {str(e)}")

            finally:
                with task_lock:
                    task = generation_tasks[task_id]
                    completed_count = len(task['results']) + len(task['errors'])
                    task_total = task.get('total', len(topics))
                    task['progress'] = (completed_count / task_total) * 100 if task_total > 0 else 0

        with task_lock:
            task = generation_tasks[task_id]
            completed_count = len(task['results']) + len(task['errors'])
            if completed_count >= task.get('total', 0):
                task['status'] = 'completed'
                print(f"✓ 任务完成! 总结果: {len(task['results'])} 成功, {len(task['errors'])} 失败")


def create_generation_task(topics, topic_images, config):
    """创建新的生成任务"""
    task_id = str(uuid.uuid4())
    with task_lock:
        generation_tasks[task_id] = {
            'status': 'running',
            'progress': 0,
            'results': [],
            'errors': [],
            'total': len(topics),
            'topic_images': topic_images
        }

    # 提交到线程池执行
    executor.submit(execute_generation_task, task_id, topics, config)
    return task_id


def get_task_status(task_id):
    """获取任务状态"""
    with task_lock:
        task = generation_tasks.get(task_id)
        if not task:
            return None
        return task.copy()


def retry_failed_topics_in_task(task_id, topics_to_retry, config):
    """重试任务中失败的主题"""
    with task_lock:
        task = generation_tasks.get(task_id)
        if not task:
            return False

        new_errors = [e for e in task['errors'] if e['topic'] not in topics_to_retry]
        task['errors'] = new_errors
        task['status'] = 'running'

        completed_count = len(task['results']) + len(task['errors'])
        if task.get('total', 0) > 0:
            task['progress'] = (completed_count / task['total']) * 100
        else:
            task['progress'] = 0

    executor.submit(execute_generation_task, task_id, topics_to_retry, config)
    return True
