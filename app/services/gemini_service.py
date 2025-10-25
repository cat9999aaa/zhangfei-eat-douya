"""Gemini API 服务模块"""

import requests
from app.utils.parsers import parse_json_response
from app.utils.validators import normalize_field
from app.config import VISUAL_TEMPLATE_PRESETS


def generate_article_with_gemini(topic, api_key, base_url, model_name, custom_prompt=''):
    """使用 Gemini API 生成文章"""
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

❌ 严格禁止以下元素：
- 不要描述任何包含文字的物品（书籍、海报、标语、杂志、报纸、标识牌、横幅、广告牌、屏幕文字、图表、数据可视化等）
- 如果内容涉及文字信息或数据，请转换为视觉象征或隐喻场景
- 专注于"可以拍照但看不到文字"的纯视觉场景

✓ 推荐场景类型：
- 自然景观、城市风光、建筑外观
- 人物动作、表情、互动场景
- 物品、设备的外观（但不要显示屏幕上的内容）
- 氛围场景、光影效果

示例对比：
✓ 正确："现代办公室中，商务人士围坐讨论，落地窗外城市天际线"
✗ 错误："商务人士查看数据报告和统计图表"（会生成带文字的图表）

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

            # 为了进一步确保图片生成时不包含文字，在摘要后添加明确指示
            # 这是双重保障：既在生成摘要时要求避免文字，又在最终提示词中再次强调
            enhanced_summary = f"{summary}，纯视觉场景，无任何文字或符号"

            print(f"段落摘要生成成功: {summary}")
            print(f"增强后的提示词: {enhanced_summary}")
            return enhanced_summary
        else:
            raise Exception('无法从API响应中提取摘要')
    except Exception as e:
        print(f"段落摘要生成失败: {e}，使用降级方案")
        # 降级：使用段落前50字符，并添加无文字指示
        fallback = paragraph_text[:50].strip()
        if fallback:
            return f"illustration of {fallback}，纯视觉场景，无任何文字或符号"
        return f"visual representation of {topic}，纯视觉场景，无任何文字或符号"


def test_gemini_model(model_name, api_key, base_url):
    """测试 Gemini 模型连接"""
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
        return False, 'API Key 无效或已过期'
    elif response.status_code == 403:
        return False, '权限不足或配额已用完'
    elif response.status_code == 404:
        return False, f'模型 {model_name} 不存在'

    response.raise_for_status()

    result = response.json()

    if 'candidates' in result and len(result['candidates']) > 0:
        reply = result['candidates'][0]['content']['parts'][0]['text']
        return True, reply[:100] + ('...' if len(reply) > 100 else '')
    else:
        return False, '模型返回了空响应'


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
