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
from app.services.gemini_service import generate_article_with_gemini, generate_visual_blueprint, build_visual_prompts, summarize_paragraph_for_image, format_article_with_citations
from app.services.document_service import extract_paragraph_structures, compute_image_slots, create_word_document
from app.services.comfyui_service import generate_image_with_comfyui
from app.services.gemini_image_service import generate_image_with_gemini, analyze_topic_for_image_generation
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
    """为单篇文章管理图片获取，确保图片唯一性"""
    def __init__(self, keyword, config, topic, visual_prompts, blueprint, topic_analysis=None):
        self.keyword = keyword
        self.config = config
        self.topic = topic
        self.visual_prompts = visual_prompts
        self.blueprint = blueprint
        self.topic_analysis = topic_analysis  # 主题分析结果
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

                    # 如果有主题分析结果，使用智能推荐的参数
                    if self.topic_analysis:
                        style = self.topic_analysis.get('style', self.gemini_image_settings.get('style', 'realistic'))
                        ethnicity = self.topic_analysis.get('ethnicity', self.gemini_image_settings.get('ethnicity', 'auto'))
                        print(f"  🎯 使用智能分析参数: 风格={style}, 人物种族={ethnicity}")
                    else:
                        style = self.gemini_image_settings.get('style', 'realistic')
                        ethnicity = self.gemini_image_settings.get('ethnicity', 'auto')

                    # 过滤掉 enabled 参数，只传递函数需要的参数
                    gemini_params = {
                        'api_key': self.gemini_image_settings.get('api_key'),
                        'base_url': self.gemini_image_settings.get('base_url', 'https://generativelanguage.googleapis.com'),
                        'model': self.gemini_image_settings.get('model', 'gemini-2.0-flash-exp'),
                        'style': style,
                        'aspect_ratio': self.gemini_image_settings.get('aspect_ratio', '16:9'),
                        'custom_style_prefix': self.gemini_image_settings.get('custom_prefix', ''),
                        'custom_style_suffix': self.gemini_image_settings.get('custom_suffix', ''),
                        'ethnicity': ethnicity,
                        'max_retries': self.gemini_image_settings.get('max_retries', 3),
                        'timeout': self.gemini_image_settings.get('timeout', 30),
                        'topic_analysis': self.topic_analysis  # 传递主题分析结果
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
    temperature = config.get('temperature', 1.0)
    top_p = config.get('top_p', 0.95)
    enable_image = config.get('enable_image', True)
    target_image_count = config.get('comfyui_image_count', 1)
    enable_search = config.get('enable_google_search', True)  # 默认启用搜索

    print(f"📄 生成文章内容...")
    print(f"   使用参数: Temperature={temperature}, Top-P={top_p}, 启用搜索={enable_search}")
    article, grounding_sources = generate_article_with_gemini(topic, gemini_api_key, gemini_base_url, model_name, custom_prompt, temperature, top_p, enable_search)

    article_title = extract_article_title(article)
    print(f"✓ 文章生成完成: 《{article_title}》")

    # 提取段落结构和小标题位置
    paragraphs, headings = extract_paragraph_structures(article)
    print(f"📊 文章结构: {len(paragraphs)} 个段落, {len(headings)} 个小标题")

    # 计算图片插入位置（基于小标题）
    image_slots = compute_image_slots(paragraphs, target_image_count, headings)
    print(f"🖼️  图片插入位置: {image_slots}")

    image_list, images_metadata = [], []

    if enable_image:
        print(f"\n🖼️  准备生成 {target_image_count} 张图片...")
        user_image_count = len(user_uploaded_images) if user_uploaded_images else 0
        need_generate_count = target_image_count - user_image_count

        for i, user_img in enumerate(user_uploaded_images or []):
            if i < len(image_slots):
                image_list.append({
                    'path': user_img.get('path'),
                    'summary': user_img.get('summary', '配图'),
                    'insert_line': image_slots[i],  # 使用行号而不是段落索引
                    'source': 'user_uploaded',
                    'order': i
                })
                images_metadata.append({'source': 'user_uploaded', 'path': user_img.get('path'), 'order': i})

        if need_generate_count > 0:
            try:
                visual_blueprint = generate_visual_blueprint(topic, article, gemini_api_key, gemini_base_url, model_name)
                visual_prompts = build_visual_prompts(visual_blueprint)
                image_keyword = derive_keyword_from_blueprint(visual_blueprint)
            except Exception:
                visual_blueprint, visual_prompts, image_keyword = None, None, ''

            # 智能主题分析（如果启用）
            topic_analysis = None
            gemini_image_settings = get_gemini_image_settings(config)
            auto_detect_topic = gemini_image_settings.get('auto_detect_topic', True)  # 默认启用
            if auto_detect_topic:
                try:
                    # 使用配置中的摘要模型
                    analysis_model = config.get('comfyui_summary_model', 'gemini-2.0-flash-exp')

                    print(f"\n🔍 智能主题分析...")
                    print(f"   主题: {topic}")
                    print(f"   使用模型: {analysis_model}")
                    topic_analysis = analyze_topic_for_image_generation(
                        topic,
                        article,
                        gemini_api_key,
                        gemini_base_url,
                        analysis_model
                    )
                    if topic_analysis:
                        print(f"✓ 主题分析成功")
                    else:
                        print(f"⚠️  主题分析返回None，使用默认参数")
                except Exception as e:
                    print(f"⚠️  主题分析失败，使用默认参数")
                    print(f"   错误详情: {e}")
                    import traceback
                    traceback.print_exc()
                    topic_analysis = None
            else:
                print(f"\n💡 智能主题检测已关闭，使用手动配置")

            image_provider = ImageProvider(image_keyword, config, topic, visual_prompts, visual_blueprint, topic_analysis)
            for i in range(user_image_count, target_image_count):
                print(f"\n  [{i+1}/{target_image_count}] 获取图片...")
                slot_index = image_slots[i] if i < len(image_slots) else None

                # 第一张图使用全文主题，其余使用段落主题
                is_first_image = (i == user_image_count)
                if is_first_image:
                    # 第一张图：使用全文主题
                    para_summary = f"visual representation of {topic}"
                    print(f"  📰 第一张图使用全文主题")
                else:
                    # 其余图片：使用段落主题
                    para_summary = f"visual representation of {topic}"
                    if slot_index is not None and slot_index < len(paragraphs):
                        para_summary = summarize_paragraph_for_image(paragraphs[slot_index]['text'], topic, config)
                        print(f"  📄 使用段落主题")

                # 第一张图使用增强提示词，让它更惊艳
                if is_first_image:
                    # 第一张图增强：添加高质量、电影感、专业摄影等关键词
                    enhanced_prompt = (
                        f"stunning masterpiece, award-winning photography, cinematic lighting, "
                        f"ultra detailed, 8k uhd, professional camera, dramatic composition, "
                        f"{para_summary}, "
                        f"high dynamic range, sharp focus, perfect exposure, magazine cover quality"
                    )
                    print(f"  🌟 使用增强质量提示词")
                else:
                    enhanced_prompt = para_summary

                custom_prompts = {
                    'positive_prompt': enhanced_prompt,
                    'negative_prompt': visual_prompts.get('negative_prompt', 'lowres, blurry, watermark') if visual_prompts else 'lowres, blurry, watermark',
                    'is_first_image': is_first_image  # 标记是否第一张图
                }
                image_path, image_source, image_metadata = image_provider.get_image(custom_prompts)

                if image_path:
                    # 获取对应的插入行号
                    insert_line = image_slots[i] if i < len(image_slots) else None
                    image_list.append({
                        'path': image_path,
                        'summary': para_summary,
                        'insert_line': insert_line,  # 使用行号而不是段落索引
                        'source': image_source,
                        'order': i
                    })
                    images_metadata.append({
                        'source': image_source,
                        'path': image_path,
                        'summary': para_summary,
                        'insert_line': insert_line,
                        'order': i,
                        'metadata': image_metadata
                    })
                    print(f"  ✓ 图片 {i+1} 获取成功（插入位置: 第{insert_line}行后）")

        print(f"\n✓ 图片准备完成，共 {len(image_list)} 张")

    # 如果启用引用链接功能，在所有图片处理完成后、生成文档前，添加参考资料
    append_citations = config.get('append_citations', False)
    if append_citations and grounding_sources:
        print(f"\n📚 添加引用链接到文章末尾...")
        print(f"   引用来源数量: {len(grounding_sources)}")
        article = format_article_with_citations(article, grounding_sources)
        print(f"✓ 引用链接已添加")
    elif append_citations and not grounding_sources:
        print(f"\n⚠️  已启用引用功能，但本次生成没有搜索来源")
    else:
        print(f"\n💡 引用功能未启用 (append_citations={append_citations})")

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

    max_retry_attempts = config.get('max_retry_attempts', 10)

    with ThreadPoolExecutor(max_workers=config.get('max_concurrent_tasks', 3)) as single_task_executor:
        futures = {single_task_executor.submit(execute_single_article_generation, topic, config, topic_images.get(topic)): topic for topic in topics}
        for future in as_completed(futures):
            topic = futures[future]
            try:
                result = future.result()
                with task_lock:
                    task = generation_tasks[task_id]

                    # ✅ 防止重复：检查该主题是否已经成功生成过
                    existing_topics = {r['topic'] for r in task['results']}
                    if topic in existing_topics:
                        print(f"⚠️  警告: 主题 '{topic}' 已经成功生成过，跳过重复结果")
                        continue

                    # 添加新结果
                    task['results'].append(result)
                    print(f"✓ 主题 '{topic}' 生成成功并记录")

            except Exception as e:
                with task_lock:
                    task = generation_tasks[task_id]
                    retry_count = task.get('retry_counts', {}).get(topic, 0)

                    # 检查是否需要自动重试
                    if retry_count < max_retry_attempts:
                        # 增加重试计数
                        task['retry_counts'][topic] = retry_count + 1
                        print(f"\n🔄 主题 '{topic}' 生成失败（第 {retry_count + 1}/{max_retry_attempts} 次尝试），正在自动重试...")
                        print(f"   错误信息: {str(e)}\n")

                        # 同步重试（不使用多线程，避免重复发布）
                        retry_success = False
                        for attempt in range(retry_count + 1, max_retry_attempts + 1):
                            try:
                                with task_lock:
                                    task['retry_counts'][topic] = attempt

                                print(f"🔄 第 {attempt}/{max_retry_attempts} 次尝试生成 '{topic}'...")
                                result = execute_single_article_generation(topic, config, topic_images.get(topic))

                                # 重试成功
                                with task_lock:
                                    task = generation_tasks[task_id]
                                    existing_topics = {r['topic'] for r in task['results']}
                                    if topic not in existing_topics:
                                        task['results'].append(result)
                                        print(f"✓ 主题 '{topic}' 在第 {attempt} 次尝试后生成成功！")
                                        retry_success = True
                                        break
                                    else:
                                        print(f"⚠️  警告: 主题 '{topic}' 已经成功生成过，跳过重复结果")
                                        retry_success = True
                                        break
                            except Exception as retry_error:
                                print(f"✗ 第 {attempt}/{max_retry_attempts} 次尝试失败: {str(retry_error)}")
                                if attempt < max_retry_attempts:
                                    print(f"   继续重试...\n")
                                else:
                                    print(f"   已达到最大重试次数，标记为失败\n")
                                    # 达到最大重试次数，记录错误
                                    with task_lock:
                                        task = generation_tasks[task_id]
                                        existing_error_topics = {err['topic'] for err in task['errors']}
                                        if topic not in existing_error_topics:
                                            task['errors'].append({
                                                'topic': topic,
                                                'error': f"尝试 {max_retry_attempts} 次后仍然失败。最后错误: {str(retry_error)}",
                                                'retry_count': max_retry_attempts
                                            })
                                            print(f"✗ 主题 '{topic}' 已尝试 {max_retry_attempts} 次，最终失败")
                    else:
                        # 已达到最大重试次数
                        existing_error_topics = {err['topic'] for err in task['errors']}
                        if topic in existing_error_topics:
                            # 更新现有错误记录
                            for err in task['errors']:
                                if err['topic'] == topic:
                                    err['error'] = str(e)
                                    err['retry_count'] = retry_count
                                    break
                            print(f"✗ 主题 '{topic}' 再次失败，已更新错误记录")
                        else:
                            # 添加新错误记录
                            task['errors'].append({'topic': topic, 'error': str(e), 'retry_count': retry_count})
                            print(f"✗ 主题 '{topic}' 生成失败并记录")

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

        # ✅ 安全检查：确保没有重复
        unique_success_topics = {r['topic'] for r in task['results']}
        unique_error_topics = {e['topic'] for e in task['errors']}

        if len(task['results']) != len(unique_success_topics):
            print(f"⚠️  警告: 检测到 {len(task['results']) - len(unique_success_topics)} 个重复的成功结果，正在去重...")
            # 去重：保留每个主题的第一个结果
            seen = set()
            deduped_results = []
            for r in task['results']:
                if r['topic'] not in seen:
                    seen.add(r['topic'])
                    deduped_results.append(r)
            task['results'] = deduped_results
            print(f"✓ 去重完成，剩余 {len(task['results'])} 个唯一结果")

        # 重新计算最终进度并检查是否完成
        completed_count = len(task['results']) + len(task['errors'])
        task['progress'] = (completed_count / task['total']) * 100 if task['total'] > 0 else 0
        if completed_count >= task['total']:
            task['status'] = 'completed'
            print(f"✓ 任务完成! 总结果: {len(task['results'])} 成功, {len(task['errors'])} 失败")
            print(f"  成功主题: {sorted([r['topic'] for r in task['results']])}")
            print(f"  失败主题: {sorted([e['topic'] for e in task['errors']])}")

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
    """重试失败的主题"""
    with task_lock:
        task = generation_tasks.get(task_id)
        if not task:
            print(f"⚠️  任务 {task_id} 不存在，创建新任务")
            new_task_id = str(uuid.uuid4())
            new_retry_counts = {topic: 1 for topic in topics_to_retry}
            generation_tasks[new_task_id] = {
                'task_id': new_task_id,
                'status': 'running',
                'total': len(topics_to_retry),
                'progress': 0,
                'results': [],
                'errors': [],
                'topic_images': {},
                'retry_counts': new_retry_counts,
                'created_at': datetime.now().isoformat()
            }
            executor.submit(execute_generation_task, new_task_id, topics_to_retry, config)
            return {'new_task': True, 'task_id': new_task_id}

        # ✅ 过滤：只重试真正失败的主题（排除已成功的）
        existing_success_topics = {r['topic'] for r in task['results']}
        actual_failed_topics = [t for t in topics_to_retry if t not in existing_success_topics]

        if not actual_failed_topics:
            print(f"⚠️  所有要重试的主题都已成功，无需重试")
            return {'success': True, 'task_id': task_id, 'skipped': True}

        if len(actual_failed_topics) < len(topics_to_retry):
            skipped = set(topics_to_retry) - set(actual_failed_topics)
            print(f"⚠️  跳过已成功的主题: {skipped}")

        # 从错误列表中移除要重试的主题
        task['errors'] = [e for e in task['errors'] if e['topic'] not in actual_failed_topics]

        # 更新重试计数
        if 'retry_counts' not in task:
            task['retry_counts'] = {}
        for topic in actual_failed_topics:
            task['retry_counts'][topic] = task['retry_counts'].get(topic, 0) + 1

        # 设置任务状态
        task['status'] = 'running'
        completed_count = len(task['results']) + len(task['errors'])
        task['progress'] = (completed_count / task['total']) * 100 if task['total'] > 0 else 0

        print(f"🔄 重试 {len(actual_failed_topics)} 个失败主题: {actual_failed_topics}")

    executor.submit(execute_generation_task, task_id, actual_failed_topics, config)
    return {'success': True, 'task_id': task_id}
