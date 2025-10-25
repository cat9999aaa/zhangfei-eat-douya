"""任务管理服务模块"""

import threading
import requests
import os
import uuid
import random
import atexit
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.config import ALLOWED_EXTENSIONS
from app.config.loader import load_config, get_comfyui_settings, get_gemini_image_settings
from app.utils.parsers import extract_article_title, derive_keyword_from_blueprint
from app.services.gemini_service import generate_article_with_gemini, generate_visual_blueprint, build_visual_prompts, summarize_paragraph_for_image
from app.services.document_service import extract_paragraph_structures, compute_image_slots, create_word_document
from app.services.comfyui_service import generate_image_with_comfyui
from app.services.gemini_image_service import generate_image_with_gemini
from app.services.image_service import (
    fetch_unsplash_image_urls, fetch_pexels_image_urls, fetch_pixabay_image_urls,
    get_local_image_paths, _download_and_save_image
)

# --- 全局变量 ---
generation_tasks = {}
task_lock = threading.Lock()
executor = ThreadPoolExecutor(max_workers=3)

@atexit.register
def shutdown_executor():
    """在应用退出时安全关闭线程池"""
    global executor
    if executor:
        try:
            print("正在关闭后台任务线程池...")
            # 使用 wait=False 避免在关闭时阻塞过久
            executor.shutdown(wait=False)
            print("线程池已关闭。")
        except Exception as e:
            print(f"关闭线程池时出现错误（可忽略）: {e}")
        finally:
            executor = None

class ImageProvider:
    # ... (内容未改变，为简洁省略) ...
    """为单篇文章管理图片获取，确保图片唯一性"""
    def __init__(self, keyword, config, topic, visual_prompts, blueprint):
        self.keyword = keyword
        self.config = config
        self.topic = topic
        self.visual_prompts = visual_prompts
        self.blueprint = blueprint
        self.comfy_settings = get_comfyui_settings(config)
        self.gemini_image_settings = get_gemini_image_settings(config)
        self.priority = config.get('image_source_priority', ['gemini_image', 'comfyui', 'user_uploaded', 'pexels', 'unsplash', 'pixabay', 'local'])
        self.tags = keyword.lower().split() if keyword else []
        self.candidates = {}  # 按需获取，缓存已获取的候选
        self.used_candidates = set()  # 记录已使用的图片，避免重复

    def _fetch_candidates_for_source(self, source):
        """按需获取指定源的候选图片"""
        # 如果已经获取过，直接返回
        if source in self.candidates:
            return self.candidates[source]

        # 根据源类型获取候选
        if source == 'unsplash' and self.config.get('unsplash_access_key') and self.keyword:
            print(f"  → 从 Unsplash 获取候选图片...")
            candidates = fetch_unsplash_image_urls(self.keyword, self.config.get('unsplash_access_key'))
            random.shuffle(candidates)
            self.candidates['unsplash'] = candidates
            print(f"  ✓ 获取了 {len(candidates)} 张候选图片")
            return candidates

        elif source == 'pexels' and self.config.get('pexels_api_key') and self.keyword:
            print(f"  → 从 Pexels 获取候选图片...")
            candidates = fetch_pexels_image_urls(self.keyword, self.config.get('pexels_api_key'))
            random.shuffle(candidates)
            self.candidates['pexels'] = candidates
            print(f"  ✓ 获取了 {len(candidates)} 张候选图片")
            return candidates

        elif source == 'pixabay' and self.config.get('pixabay_api_key') and self.keyword:
            print(f"  → 从 Pixabay 获取候选图片...")
            candidates = fetch_pixabay_image_urls(self.keyword, self.config.get('pixabay_api_key'))
            random.shuffle(candidates)
            self.candidates['pixabay'] = candidates
            print(f"  ✓ 获取了 {len(candidates)} 张候选图片")
            return candidates

        elif source == 'local':
            print(f"  → 从本地图库获取候选图片...")
            candidates = get_local_image_paths(self.tags, self.config)
            random.shuffle(candidates)
            self.candidates['local'] = candidates
            print(f"  ✓ 获取了 {len(candidates)} 张候选图片")
            return candidates

        # 不支持的源或配置不完整
        return []

    def get_image(self, custom_prompts):
        """按照优先级顺序获取图片"""
        # 源名称映射（统一定义，避免重复）
        source_names = {
            'user_uploaded': '用户上传',
            'gemini_image': 'Gemini生图',
            'comfyui': 'ComfyUI',
            'unsplash': 'Unsplash',
            'pexels': 'Pexels',
            'pixabay': 'Pixabay',
            'local': '本地图库'
        }

        # 显示当前使用的优先级顺序（仅第一次）
        if not hasattr(self, '_priority_logged'):
            priority_display = ' > '.join([source_names.get(s, s) for s in self.priority])
            print(f"\n📋 图片源优先级: {priority_display}\n")
            self._priority_logged = True

        for source in self.priority:
            try:
                # Gemini 图片生成
                if source == 'gemini_image':
                    if not self.gemini_image_settings.get('enabled', True):
                        print(f"  ✗ Gemini 图像生成已禁用，跳过")
                        continue

                    api_key = self.gemini_image_settings.get('api_key')
                    if not api_key:
                        print(f"  ✗ Gemini 图像生成未配置 API Key，跳过")
                        continue

                    print(f"→ 尝试使用 Gemini 生成图片...")
                    prompt = custom_prompts.get('positive_prompt', self.topic or "beautiful image")
                    # 过滤掉 enabled 参数，只传递函数需要的参数
                    gemini_params = {
                        'api_key': self.gemini_image_settings.get('api_key'),
                        'base_url': self.gemini_image_settings.get('base_url', 'https://generativelanguage.googleapis.com'),
                        'model': self.gemini_image_settings.get('model', 'gemini-2.0-flash-exp'),
                        'style': self.gemini_image_settings.get('style', 'realistic'),
                        'aspect_ratio': self.gemini_image_settings.get('aspect_ratio', '16:9'),
                        'custom_style_prefix': self.gemini_image_settings.get('custom_prefix', ''),
                        'custom_style_suffix': self.gemini_image_settings.get('custom_suffix', ''),
                        'max_retries': self.gemini_image_settings.get('max_retries', 3),
                        'timeout': self.gemini_image_settings.get('timeout', 30)
                    }
                    image_path, metadata = generate_image_with_gemini(prompt=prompt, **gemini_params)
                    if image_path:
                        print(f"✓ 使用 Gemini 生成图片成功")
                        return image_path, 'gemini_image', metadata
                    else:
                        print(f"  ✗ Gemini 生成失败（返回 None），继续尝试下一个源...")

                # ComfyUI 图片生成
                elif source == 'comfyui':
                    if not self.comfy_settings.get('enabled', True):
                        print(f"  ✗ ComfyUI 已禁用，跳过")
                        continue

                    # 检查必要条件
                    if not self.comfy_settings.get('workflow_path'):
                        print(f"  ✗ ComfyUI 未配置 workflow 路径，跳过")
                        continue

                    if not self.visual_prompts:
                        print(f"  ✗ ComfyUI 需要视觉提示词，但生成失败，跳过")
                        continue

                    if not self.topic:
                        print(f"  ✗ ComfyUI 需要主题信息，但未提供，跳过")
                        continue

                    # 所有条件满足，尝试生成
                    print(f"→ 尝试使用 ComfyUI 生成图片...")
                    image_path, metadata = generate_image_with_comfyui(self.topic, custom_prompts, self.blueprint, self.config, self.comfy_settings)
                    if image_path:
                        print(f"✓ 使用 ComfyUI 生成图片成功")
                        return image_path, 'comfyui', metadata
                    else:
                        print(f"  ✗ ComfyUI 生成失败，继续尝试下一个源...")

                # 用户上传的图片
                elif source == 'user_uploaded':
                    # user_uploaded 由主流程直接处理，这里不需要额外处理
                    pass

                # API 图片源和本地图库（按需获取）
                elif source in ['unsplash', 'pexels', 'pixabay', 'local']:
                    source_name_map = {
                        'unsplash': 'Unsplash',
                        'pexels': 'Pexels',
                        'pixabay': 'Pixabay',
                        'local': '本地图库'
                    }

                    # 按需获取候选图片
                    candidates = self._fetch_candidates_for_source(source)

                    if not candidates:
                        print(f"  ✗ {source_name_map.get(source, source)} 无可用图片，跳过")
                        continue

                    # 从候选中选择一张未使用的图片
                    while candidates:
                        candidate = candidates.pop(0)
                        if candidate not in self.used_candidates:
                            self.used_candidates.add(candidate)
                            if source == 'local':
                                print(f"  ✓ 使用 {source_name_map.get(source, source)} 图片")
                                return candidate, 'local', {}
                            else:
                                image_path = _download_and_save_image(candidate)
                                if image_path:
                                    print(f"  ✓ 使用 {source_name_map.get(source, source)} 图片")
                                    return image_path, source, {}

                    # 如果所有候选都已使用
                    print(f"  ✗ {source_name_map.get(source, source)} 的图片已全部使用，跳过")
            except Exception as e:
                source_name = source_names.get(source, source)
                print(f"✗ {source_name} 发生异常: {e}")
                import traceback
                traceback.print_exc()
                print(f"  继续尝试下一个图片源...")

        print(f"\n✗ 所有图片源均已尝试，未能获取图片")
        print(f"   已尝试的顺序: {' > '.join([source_names.get(s, s) for s in self.priority])}\n")
        return None, 'none', {}

def update_executor_workers(max_workers=3):
    """更新线程池的工作线程数"""
    global executor
    if executor:
        executor.shutdown(wait=True)
    executor = ThreadPoolExecutor(max_workers=max_workers)
    print(f"线程池已更新，最大并发数: {max_workers}")

def execute_single_article_generation(topic, config, user_uploaded_images=None):
    """
    生成单篇文章

    Args:
        topic: 文章主题
        config: 配置信息
        user_uploaded_images: 用户上传的图片列表

    Returns:
        dict: 生成结果
    """
    print(f"\n{'='*60}")
    print(f"📝 开始生成文章")
    print(f"   主题: {topic}")
    print(f"{'='*60}\n")

    gemini_api_key = config.get('gemini_api_key', '')
    gemini_base_url = config.get('gemini_base_url', 'https://generativelanguage.googleapis.com')
    pandoc_path = config.get('pandoc_path', '')
    model_name = config.get('default_model') or 'gemini-pro'
    custom_prompt = config.get('default_prompt', '')
    enable_image = config.get('enable_image', True)
    target_image_count = config.get('comfyui_image_count', 1)

    print(f"📄 生成文章内容...")
    article = generate_article_with_gemini(topic, gemini_api_key, gemini_base_url, model_name, custom_prompt)
    article_title = extract_article_title(article)
    print(f"✓ 文章生成完成: 《{article_title}》")

    paragraphs = extract_paragraph_structures(article)
    image_slots = compute_image_slots(paragraphs, target_image_count)
    image_list, images_metadata = [], []

    if enable_image:
        print(f"\n🖼️  准备生成 {target_image_count} 张图片...")
        user_image_count = len(user_uploaded_images) if user_uploaded_images else 0
        need_generate_count = target_image_count - user_image_count

        for i, user_img in enumerate(user_uploaded_images or []):
            if i < len(image_slots):
                image_list.append({'path': user_img.get('path'), 'summary': user_img.get('summary', '配图'), 'paragraph_index': image_slots[i], 'source': 'user_uploaded', 'order': i})
                images_metadata.append({'source': 'user_uploaded', 'path': user_img.get('path'), 'order': i})

        if need_generate_count > 0:
            try:
                visual_blueprint = generate_visual_blueprint(topic, article, gemini_api_key, gemini_base_url, model_name)
                visual_prompts = build_visual_prompts(visual_blueprint)
                image_keyword = derive_keyword_from_blueprint(visual_blueprint)
            except Exception:
                visual_blueprint, visual_prompts, image_keyword = None, None, ''

            image_provider = ImageProvider(image_keyword, config, topic, visual_prompts, visual_blueprint)
            for i in range(user_image_count, target_image_count):
                print(f"\n  [{i+1}/{target_image_count}] 获取图片...")
                slot_index = image_slots[i] if i < len(image_slots) else None
                para_summary = f"visual representation of {topic}"
                if slot_index is not None and slot_index < len(paragraphs):
                    para_summary = summarize_paragraph_for_image(paragraphs[slot_index]['text'], topic, config)

                custom_prompts = {'positive_prompt': para_summary, 'negative_prompt': visual_prompts.get('negative_prompt', 'lowres, blurry, watermark') if visual_prompts else 'lowres, blurry, watermark'}
                image_path, image_source, image_metadata = image_provider.get_image(custom_prompts)

                if image_path:
                    image_list.append({'path': image_path, 'summary': para_summary, 'paragraph_index': slot_index, 'source': image_source, 'order': i})
                    images_metadata.append({'source': image_source, 'path': image_path, 'summary': para_summary, 'paragraph_index': slot_index, 'order': i, 'metadata': image_metadata})
                    print(f"  ✓ 图片 {i+1} 获取成功")

        print(f"\n✓ 图片准备完成，共 {len(image_list)} 张")

    print(f"\n📦 生成 Word 文档...")
    filename = create_word_document(article_title, article, image_list, enable_image, pandoc_path, config)
    print(f"✓ 文档生成完成: {filename}")
    print(f"\n{'='*60}")
    print(f"✅ 文章《{article_title}》生成成功")
    print(f"{'='*60}\n")

    return {'success': True, 'topic': topic, 'article_title': article_title, 'filename': filename, 'image_count': len(image_list), 'images_info': images_metadata, 'has_image': len(image_list) > 0}

def execute_generation_task(task_id, topics, config):
    """为给定的主题列表执行生成，并确保所有主题都有最终状态。"""
    with task_lock:
        task = generation_tasks.get(task_id, {})
        topic_images = task.get('topic_images', {})

    with ThreadPoolExecutor(max_workers=config.get('max_concurrent_tasks', 3)) as single_task_executor:
        futures = {single_task_executor.submit(execute_single_article_generation, topic, config, topic_images.get(topic)): topic for topic in topics}
        for future in as_completed(futures):
            topic = futures[future]
            try:
                result = future.result()
                with task_lock:
                    generation_tasks[task_id]['results'].append(result)
            except Exception as e:
                with task_lock:
                    task = generation_tasks[task_id]
                    retry_count = task.get('retry_counts', {}).get(topic, 0)
                    task['errors'].append({'topic': topic, 'error': str(e), 'retry_count': retry_count})
            finally:
                with task_lock:
                    task = generation_tasks[task_id]
                    completed_count = len(task['results']) + len(task['errors'])
                    task['progress'] = (completed_count / task['total']) * 100 if task['total'] > 0 else 0

    # --- 任务核对机制 ---
    with task_lock:
        task = generation_tasks[task_id]
        processed_topics = {r['topic'] for r in task['results']} | {e['topic'] for e in task['errors']}
        initial_topics_for_this_run = set(topics)
        missing_topics = initial_topics_for_this_run - processed_topics

        if missing_topics:
            print(f"核对发现 {len(missing_topics)} 个幽灵任务: {missing_topics}")
            for topic in missing_topics:
                retry_count = task.get('retry_counts', {}).get(topic, 0)
                task['errors'].append({
                    'topic': topic,
                    'error': '任务在执行过程中意外中断或超时',
                    'retry_count': retry_count
                })

        # 重新计算最终进度并检查是否完成
        completed_count = len(task['results']) + len(task['errors'])
        task['progress'] = (completed_count / task['total']) * 100 if task['total'] > 0 else 0
        if completed_count >= task['total']:
            task['status'] = 'completed'
            print(f"✓ 任务完成! 总结果: {len(task['results'])} 成功, {len(task['errors'])} 失败")

def create_generation_task(topics, topic_images, config):
    task_id = str(uuid.uuid4())
    with task_lock:
        generation_tasks[task_id] = {'status': 'running', 'progress': 0, 'results': [], 'errors': [], 'total': len(topics), 'topic_images': topic_images, 'retry_counts': {}}
    executor.submit(execute_generation_task, task_id, list(topics), config)
    return task_id

def get_task_status(task_id):
    with task_lock:
        return generation_tasks.get(task_id, {}).copy()

def retry_failed_topics_in_task(task_id, topics_to_retry, config):
    with task_lock:
        task = generation_tasks.get(task_id)
        if not task:
            new_task_id = str(uuid.uuid4())
            new_retry_counts = {topic: 1 for topic in topics_to_retry}
            generation_tasks[new_task_id] = {'task_id': new_task_id, 'status': 'running', 'total': len(topics_to_retry), 'progress': 0, 'results': [], 'errors': [], 'topic_images': {}, 'retry_counts': new_retry_counts, 'created_at': datetime.now().isoformat()}
            executor.submit(execute_generation_task, new_task_id, topics_to_retry, config)
            return {'new_task': True, 'task_id': new_task_id}

        task['errors'] = [e for e in task['errors'] if e['topic'] not in topics_to_retry]
        if 'retry_counts' not in task: task['retry_counts'] = {}
        for topic in topics_to_retry:
            task['retry_counts'][topic] = task['retry_counts'].get(topic, 0) + 1

        task['status'] = 'running'
        completed_count = len(task['results']) + len(task['errors'])
        task['progress'] = (completed_count / task['total']) * 100 if task['total'] > 0 else 0

    executor.submit(execute_generation_task, task_id, topics_to_retry, config)
    return {'success': True, 'task_id': task_id}
