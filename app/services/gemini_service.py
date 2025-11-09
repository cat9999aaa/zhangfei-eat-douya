"""Gemini API 服务模块"""

import requests
from app.utils.parsers import parse_json_response
from app.utils.filters import (
    is_domain_blacklisted, is_tld_whitelisted, is_static_url,
    contains_blacklisted_keyword, contains_chinese, contains_traditional_chinese,
    log_filtered_event
)
from app.utils.validators import normalize_field
from app.config import VISUAL_TEMPLATE_PRESETS
from app.utils.network import fetch_real_url_and_title


def generate_article_with_gemini(topic, api_key, base_url, model_name, custom_prompt='', temperature=1.0, top_p=0.95, enable_search=True):
    """使用 Gemini API 生成文章，支持 Google 搜索和思考过程展示"""
    import json

    # 构建提示词
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

    # 打印参数信息
    print(f"\n{'='*60}")
    print(f"🔧 Gemini API 调用参数:")
    print(f"   模型: {model_name}")
    print(f"   Temperature: {temperature}")
    print(f"   Top-P: {top_p}")
    print(f"   启用搜索: {enable_search}")
    print(f"   提示词长度: {len(prompt)} 字符")
    print(f"{'='*60}\n")

    # 打印提示词前500字符
    print(f"📝 使用的提示词（前500字符）:")
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    print(f"{'='*60}\n")

    # 构建请求数据（使用非流式 API）
    url = f'{base_url}/v1beta/models/{model_name}:generateContent?key={api_key}'
    headers = {'Content-Type': 'application/json'}

    data = {
        'contents': [{
            'parts': [{'text': prompt}]
        }],
        'generationConfig': {
            'temperature': temperature,
            'topP': top_p
        }
    }

    # 添加 Google 搜索工具（如果启用）
    if enable_search:
        data['tools'] = [{
            'googleSearch': {}
        }]
        print(f"🔍 已启用 Google 搜索功能\n")

    # 打印请求配置
    print(f"📤 实际发送给 Gemini API 的配置:")
    print(f"   URL: {url.split('?key=')[0]}?key=***")
    print(f"   请求体配置:")
    safe_data = data.copy()
    print(json.dumps(safe_data, indent=4, ensure_ascii=False))
    print(f"{'='*60}\n")

    try:
        # 发送请求
        print(f"⏳ 正在生成文章...\n")
        response = requests.post(url, headers=headers, json=data, timeout=120)

        if response.status_code != 200:
            print(f"\n❌ Gemini API 返回错误:")
            print(f"   状态码: {response.status_code}")
            print(f"   错误响应:")
            try:
                error_detail = response.json()
                print(json.dumps(error_detail, indent=6, ensure_ascii=False))
            except:
                print(f"   {response.text}")
            print(f"{'='*60}\n")

        response.raise_for_status()

        # 解析响应
        result = response.json()

        # 提取文章内容
        article_text = ""
        search_queries = []
        grounding_sources = []
        thinking_text = ""

        if 'candidates' in result and len(result['candidates']) > 0:
            candidate = result['candidates'][0]

            # 提取文本内容
            if 'content' in candidate and 'parts' in candidate['content']:
                for part in candidate['content']['parts']:
                    if 'text' in part:
                        article_text += part['text']

                    # 检查是否有思考过程
                    if 'thought' in part and part['thought']:
                        thinking_text += part['thought'] + "\n"

            # 提取搜索元数据
            if 'groundingMetadata' in candidate:
                metadata = candidate['groundingMetadata']

                # 提取搜索查询
                if 'webSearchQueries' in metadata:
                    search_queries = metadata['webSearchQueries']

                # 提取引用来源
                if 'groundingChunks' in metadata:
                    for chunk_item in metadata['groundingChunks']:
                        if 'web' in chunk_item:
                            source = {
                                'uri': chunk_item['web'].get('uri', ''),
                                'title': chunk_item['web'].get('title', '')
                            }
                            grounding_sources.append(source)

        # 显示思考过程
        if thinking_text:
            print(f"💭 模型思考过程:")
            print(thinking_text)
            print(f"{'='*60}\n")

        # 显示搜索信息
        if search_queries:
            print(f"🔍 模型执行的搜索查询:")
            for i, query in enumerate(search_queries, 1):
                print(f"   {i}. {query}")
            print()

        if grounding_sources:
            print(f"📚 引用来源 ({len(grounding_sources)} 个):")
            for i, source in enumerate(grounding_sources[:5], 1):  # 只显示前5个
                print(f"   {i}. {source['title']}")
                print(f"      {source['uri']}")
            if len(grounding_sources) > 5:
                print(f"   ... 还有 {len(grounding_sources) - 5} 个来源")
            print()

        print(f"✓ 文章生成完成")
        print(f"  - Temperature: {temperature}")
        print(f"  - Top-P: {top_p}")
        print(f"  - 文章长度: {len(article_text)} 字符")
        if search_queries:
            print(f"  - 搜索次数: {len(search_queries)}")
        if grounding_sources:
            print(f"  - 引用来源: {len(grounding_sources)} 个")
        print(f"{'='*60}\n")

        if not article_text:
            raise Exception('无法从 API 响应中提取文章内容')

        # 返回文章内容和引用来源（元组形式）
        return article_text, grounding_sources

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP 错误详情:")
        print(f"   请求的 temperature: {temperature} (类型: {type(temperature).__name__})")
        print(f"   请求的 top_p: {top_p} (类型: {type(top_p).__name__})")
        raise Exception(f"Gemini API 请求失败: {e}")
    except Exception as e:
        print(f"\n❌ 处理响应时出错: {e}")
        raise


def format_article_with_citations(article_text, grounding_sources):
    """
    在文章末尾添加参考资料引用链接，并进行智能排序和筛选
    """
    if not grounding_sources:
        return article_text

    print(f"\n🔍 开始处理 {len(grounding_sources)} 个原始引用来源...")
    processed_sources = []
    seen_urls = set()

    # 定义无效页面标题的关键词黑名单
    INVALID_TITLE_KEYWORDS = [
        '404', 'not found', '页面不存在', '找不到', 'page verification',
        'are you a robot', 'just a moment', 'checking your browser',
        '安全验证', '人机验证', '访问验证', 'login', '登录', 'error', '错误'
    ]
    for source in grounding_sources:
        original_uri = source.get('uri', '')
        if not original_uri:
            continue

        print(f"  → 正在解析: {original_uri[:70]}...")
        real_url, title, site_name, lang = fetch_real_url_and_title(original_uri)

        # --- 终极版八层过滤系统 ---
        # 1. GFWList 黑名单检查
        matched_rule = is_domain_blacklisted(real_url)
        if matched_rule:
            print(f"  ✗ [1/8] 域名在 GFWList 黑名单中，已过滤")
            log_filtered_event(real_url, "1. GFWList Blacklist", f"Matched: {matched_rule}")
            continue

        # 2. TLD 白名单检查
        if not is_tld_whitelisted(real_url):
            print(f"  ✗ [2/8] 域名后缀不在白名单内，已过滤")
            log_filtered_event(real_url, "2. TLD Whitelist", f"URL: {real_url}")
            continue

        # 3. 静态链接格式检查
        if not is_static_url(real_url):
            print(f"  ✗ [3/8] URL 非静态链接 (非 .html/.htm)，已过滤")
            log_filtered_event(real_url, "3. Non-Static URL", f"URL: {real_url}")
            continue

        # 4. 标题关键词黑名单检查
        if contains_blacklisted_keyword(title):
            print(f"  ✗ [4/8] 标题包含黑名单关键词，已过滤")
            log_filtered_event(real_url, "4. Title Keyword Blacklist", f"Title: {title}")
            continue

        # 5. 严格独立内容审查 (网站名)
        if not contains_chinese(site_name):
            print(f"  ✗ [5/8] 网站名称不含中文 (纯英文或乱码)，已过滤")
            log_filtered_event(real_url, "5. Invalid Site Name (No Chinese)", f"Site Name: {site_name}")
            continue
        if contains_traditional_chinese(site_name):
            print(f"  ✗ [5/8] 网站名称检测到繁体字，已过滤")
            log_filtered_event(real_url, "5. Traditional Chinese in Site Name", f"Site Name: {site_name}")
            continue

        # 6. 严格独立内容审查 (标题)
        if not contains_chinese(title):
            print(f"  ✗ [6/8] 文章标题不含中文 (纯英文或乱码)，已过滤")
            log_filtered_event(real_url, "6. Invalid Title (No Chinese)", f"Title: {title}")
            continue
        if contains_traditional_chinese(title):
            print(f"  ✗ [6/8] 文章标题检测到繁体字，已过滤")
            log_filtered_event(real_url, "6. Traditional Chinese in Title", f"Title: {title}")
            continue

        # 7. 无效页面检查 (404, 登录等)
        is_invalid_title = False
        if title:
            lower_title = title.lower()
            for keyword in INVALID_TITLE_KEYWORDS:
                if keyword in lower_title:
                    is_invalid_title = True
                    break
        if is_invalid_title:
            print(f"  ✗ [7/8] 页面内容无效 (404/登录页等)，已过滤")
            log_filtered_event(real_url, "7. Invalid Page Content", f"Title: {title}")
            continue

        # 8. 重复链接检查
        if real_url in seen_urls:
            print(f"  ✗ [8/8] 检测到重复链接，已过滤")
            log_filtered_event(real_url, "8. Duplicate URL", f"URL: {real_url}")
            continue

        if real_url and title and site_name:
            processed_sources.append({
                'url': real_url,
                'title': title,
                'site_name': site_name
            })
            # 将新链接添加到已处理集合
            seen_urls.add(real_url)
            print(f"  ✓ 解析成功: {site_name} - {title}")
        else:
            print(f"  ✗ 解析失败或信息不全，跳过")

    print(f"\n⭐ 已完成高质量筛选，共找到 {len(processed_sources)} 条有效引用")

    top_sources = processed_sources[:5]
    print(f"🔪 已选取最重要的 {len(top_sources)} 条引用")

    if not top_sources:
        print("⚠️  所有引用链接解析失败，无参考资料可添加")
        return article_text

    citations_section = "\n\n---\n\n## 参考资料\n\n"
    for source in top_sources:
        # 使用 \n\n 来强制换行，确保在 Word 中也能正确显示
        citations_section += f"{source['site_name']}：{source['title']}\n\n原文链接：{source['url']}\n\n"

    print(f"\n📝 引用格式化详情:")
    print(f"   原文章长度: {len(article_text)} 字符")
    print(f"   引用部分长度: {len(citations_section)} 字符")
    print(f"   引用内容预览:")
    print(citations_section[:200] + "..." if len(citations_section) > 200 else citations_section)

    final_article = article_text + citations_section
    print(f"   最终文章长度: {len(final_article)} 字符")

    return final_article


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
        blueprint = parse_json_response(raw_text)
    except ValueError as exc:
        raise Exception(f'视觉描述 JSON 解析失败: {exc}')

    template = blueprint.get('template', 'editorial')
    if template not in VISUAL_TEMPLATE_PRESETS:
        template = 'editorial'

    normalized = {
        'template': template,
        'subject': normalize_field(blueprint.get('subject'), topic),
        'scene': normalize_field(blueprint.get('scene'), f'story about {topic}'),
        'mood': normalize_field(blueprint.get('mood'), 'dramatic and inspiring'),
        'style': normalize_field(blueprint.get('style'), 'cinematic, highly detailed'),
        'lighting': normalize_field(blueprint.get('lighting'), 'soft cinematic lighting'),
        'composition': normalize_field(blueprint.get('composition'), 'balanced composition'),
        'details': normalize_field(blueprint.get('details'), 'intricate storytelling details'),
        'negative': normalize_field(blueprint.get('negative'), 'lowres, blurry, distorted, watermark')
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


def summarize_paragraph_for_image(paragraph_text, topic, config):
    """为段落生成图片摘要（中文视觉描述）"""
    # 摘要模型独立配置，如果未设置则使用主写作模型作为默认值
    summary_model = config.get('comfyui_summary_model')

    # 向后兼容：如果是旧的 __default__ 值或未设置，使用主写作模型
    if not summary_model or summary_model == '__default__':
        summary_model = config.get('default_model', 'gemini-pro')

    api_key = config.get('gemini_api_key', '')
    base_url = config.get('gemini_base_url', 'https://generativelanguage.googleapis.com')

    if not api_key:
        return f"visual representation of {topic}"

    # 限制段落长度
    truncated_para = paragraph_text[:500]

    prompt = f"""阅读以下关于「{topic}」的文章段落，为其生成适合AI图片生成的中文视觉描述。

核心要求：
1. 描述段落中的主要主体、动作或场景（15-30个汉字）
2. 要具体且可视化 - 描述你会看到什么，而不是抽象概念
3. 使用具体的名词、生动的动词和具体细节
4. 聚焦于视觉元素：物体、人物、地点、动作、氛围、色彩、光线

❌ 严格禁止以下元素（这些会导致用户账号被封！）：
【绝对不能出现的内容】
- 任何军警相关：警察、军人、军队、士兵、警服、军装、制服、警徽、军徽、警车、军车、坦克、武器、枪械
- 任何政治相关：国旗、党旗、国徽、党徽、领导人、政治人物、政府建筑、天安门、人民大会堂、政治标语
- 任何敏感制服：城管、保安、执法、公务员、官员等穿制服的职业
- 任何暴力内容：打斗、血腥、战争、冲突、抗议、游行
- 任何文字图片：书籍、海报、标语、杂志、报纸、标识牌、横幅、广告牌、屏幕文字、图表、数据可视化

【如果段落内容涉及以上敏感话题】
- 完全忽略这些内容，不要描述
- 转换为普通日常生活场景：办公室、咖啡馆、街道、公园等
- 只描述普通民众的日常活动

✓ 安全的场景类型：
- 自然景观、城市风光、建筑外观（避免政府建筑）
- 普通人的日常活动：购物、用餐、交谈、休闲
- 办公室场景、咖啡馆、商场、公园
- 抽象的氛围场景、光影效果
- 静物、物品（避免武器等危险物品）

示例对比：
✓ 安全："现代办公室中，商务人士围坐讨论，落地窗外城市天际线"
✓ 安全："咖啡馆里，年轻人使用笔记本电脑工作，温暖的灯光"
✗ 危险："警察在街道巡逻"（会被封号！）
✗ 危险："军人站岗"（会被封号！）
✗ 危险："国旗飘扬"（会被封号！）

5. 只输出中文视觉描述，不要引号、标点或额外说明文字

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

            # 安全过滤：检查并移除敏感词汇
            sensitive_keywords = [
                '警察', '军人', '军队', '士兵', '警服', '军装', '制服', '警徽', '军徽',
                '警车', '军车', '坦克', '武器', '枪', '步枪', '手枪',
                '国旗', '党旗', '国徽', '党徽', '领导', '主席', '总书记',
                '天安门', '人民大会堂', '政府', '官员', '公务员',
                '城管', '保安', '执法', '巡逻', '站岗',
                '战争', '打斗', '冲突', '抗议', '游行', '示威'
            ]

            # 如果检测到敏感词，替换为安全的通用场景
            contains_sensitive = False
            for keyword in sensitive_keywords:
                if keyword in summary:
                    contains_sensitive = True
                    print(f"⚠️ 警告：检测到敏感词'{keyword}'，将替换为安全场景")
                    break

            if contains_sensitive:
                # 替换为安全的通用场景描述
                summary = "现代都市街景，行人在商业街区漫步，现代建筑林立，温暖的阳光"
                print(f"✓ 已替换为安全场景: {summary}")

            # 为了进一步确保图片生成时不包含文字和敏感内容，在摘要后添加明确指示
            enhanced_summary = f"{summary}，穿着便装的平民，日常休闲服饰，和平场景，纯视觉场景，无文字无符号无制服"

            print(f"段落摘要生成成功: {summary}")
            print(f"增强后的安全提示词: {enhanced_summary}")
            return enhanced_summary
        else:
            raise Exception('无法从API响应中提取摘要')
    except Exception as e:
        print(f"段落摘要生成失败: {e}，使用安全降级方案")
        # 降级：使用安全的通用场景，避免任何可能的敏感内容
        return f"现代都市生活场景，穿着便装的平民，日常休闲活动，和平场景，纯视觉场景，无文字无符号无制服"


def test_gemini_model(model_name, api_key, base_url, temperature=1.0, top_p=0.95):
    """测试 Gemini 模型连接"""
    test_prompt = "请用一句话介绍你自己。"

    url = f'{base_url}/v1beta/models/{model_name}:generateContent?key={api_key}'
    headers = {'Content-Type': 'application/json'}
    payload = {
        'contents': [{
            'parts': [{'text': test_prompt}]
        }],
        'generationConfig': {
            'temperature': temperature,
            'topP': top_p
        }
    }

    # 🔍 打印测试请求的配置参数
    print(f"\n📤 测试模型时发送的 generationConfig:")
    import json
    print(json.dumps(payload['generationConfig'], indent=4, ensure_ascii=False))
    print()

    response = requests.post(url, headers=headers, json=payload, timeout=30)

    if response.status_code == 401:
        return False, 'API Key 无效或已过期', {}
    elif response.status_code == 403:
        return False, '权限不足或配额已用完', {}
    elif response.status_code == 404:
        return False, f'模型 {model_name} 不存在', {}

    response.raise_for_status()

    result = response.json()

    if 'candidates' in result and len(result['candidates']) > 0:
        reply = result['candidates'][0]['content']['parts'][0]['text']
        # 返回参数信息
        params_info = {
            'temperature': temperature,
            'top_p': top_p
        }
        return True, reply[:100] + ('...' if len(reply) > 100 else ''), params_info
    else:
        return False, '模型返回了空响应', {}


def get_available_models(api_key, base_url):
    """获取可用的 Gemini 模型列表"""
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
    return model_list
