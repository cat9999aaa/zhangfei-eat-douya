"""Gemini 图像生成服务模块"""

import os
import base64
import requests
import uuid
from datetime import datetime
from app.config.loader import load_config


# Gemini 图像生成比例预设
# 支持 Gemini 2.5 Flash Image (Nano Banana) 的10种官方比例
GEMINI_IMAGE_ASPECT_RATIOS = {
    # 横向比例
    '21:9': {
        'name': '超宽屏 (21:9)',
        'prompt_hint': 'ultra-widescreen composition, 21:9 aspect ratio, cinematic panorama'
    },
    '16:9': {
        'name': '宽屏 (16:9)',
        'prompt_hint': 'widescreen composition, 16:9 aspect ratio, cinematic'
    },
    '4:3': {
        'name': '标准横屏 (4:3)',
        'prompt_hint': 'standard horizontal composition, 4:3 aspect ratio'
    },
    '3:2': {
        'name': '相机横屏 (3:2)',
        'prompt_hint': 'classic camera composition, 3:2 aspect ratio, landscape'
    },
    # 正方形
    '1:1': {
        'name': '正方形 (1:1)',
        'prompt_hint': 'square composition, 1:1 aspect ratio, balanced'
    },
    # 纵向比例
    '9:16': {
        'name': '竖屏 (9:16)',
        'prompt_hint': 'vertical composition, 9:16 aspect ratio, portrait orientation'
    },
    '3:4': {
        'name': '标准竖屏 (3:4)',
        'prompt_hint': 'standard vertical composition, 3:4 aspect ratio'
    },
    '2:3': {
        'name': '相机竖屏 (2:3)',
        'prompt_hint': 'classic camera composition, 2:3 aspect ratio, portrait'
    },
    # 弹性比例
    '5:4': {
        'name': '弹性横屏 (5:4)',
        'prompt_hint': 'flexible horizontal composition, 5:4 aspect ratio'
    },
    '4:5': {
        'name': '弹性竖屏 (4:5)',
        'prompt_hint': 'flexible vertical composition, 4:5 aspect ratio'
    }
}

# Gemini 图像生成预设风格
GEMINI_IMAGE_STYLE_PRESETS = {
    'realistic': {
        'name': '写实摄影',
        'prompt_prefix': 'Highly detailed realistic photography, natural lighting, sharp focus, professional camera, ',
        'prompt_suffix': ', photorealistic, 8k resolution, high quality, no text or words'
    },
    'illustration': {
        'name': '插画风格',
        'prompt_prefix': 'Beautiful illustration art, detailed artwork, artistic style, ',
        'prompt_suffix': ', digital painting, vibrant colors, high quality, no text or letters'
    },
    'anime': {
        'name': '动漫风格',
        'prompt_prefix': 'Anime style artwork, detailed anime art, Japanese animation style, ',
        'prompt_suffix': ', vibrant colors, clean lines, high quality anime, no text or words'
    },
    'cyberpunk': {
        'name': '赛博朋克',
        'prompt_prefix': 'Cyberpunk style, neon lights, futuristic cityscape, high-tech atmosphere, ',
        'prompt_suffix': ', dramatic lighting, neon colors, dystopian future, 8k, no text or signs'
    },
    'business': {
        'name': '商业配图',
        'prompt_prefix': 'Professional business illustration, clean design, corporate style, ',
        'prompt_suffix': ', modern aesthetic, professional quality, suitable for presentations, no text or words'
    },
    'watercolor': {
        'name': '水彩画',
        'prompt_prefix': 'Watercolor painting style, soft colors, artistic brushstrokes, ',
        'prompt_suffix': ', delicate details, flowing colors, artistic quality, no text or letters'
    },
    'minimalist': {
        'name': '极简主义',
        'prompt_prefix': 'Minimalist design, clean composition, simple shapes, ',
        'prompt_suffix': ', modern aesthetics, negative space, elegant simplicity, no text or words'
    },
    'fantasy': {
        'name': '奇幻风格',
        'prompt_prefix': 'Fantasy art, magical atmosphere, imaginative scene, ',
        'prompt_suffix': ', epic scale, mystical lighting, highly detailed, cinematic, no text or words'
    }
}


def apply_style_to_prompt(base_prompt, style='realistic', aspect_ratio='16:9', custom_prefix='', custom_suffix='', use_api_aspect_ratio=True):
    """
    将风格和比例应用到提示词上

    组合顺序（风格提示词在摘要内容之前）：
    用户自定义前缀 → 预设风格前缀 → 预设风格后缀 → [比例提示*] → 摘要内容 → 用户自定义后缀

    * 只有当 use_api_aspect_ratio=False 时才在提示词中添加比例描述
      如果通过 API 参数控制比例，则不在提示词中重复

    这样所有预设风格提示词都在摘要之前，用户自定义的前缀优先级最高
    """
    parts = []

    # 1. 用户自定义前缀（最外层，优先级最高）
    if custom_prefix:
        parts.append(custom_prefix.strip())

    # 2. 预设风格前缀
    if style in GEMINI_IMAGE_STYLE_PRESETS:
        preset_prefix = GEMINI_IMAGE_STYLE_PRESETS[style]['prompt_prefix'].strip()
        if preset_prefix:
            parts.append(preset_prefix)

    # 3. 预设风格后缀（放在摘要之前）
    if style in GEMINI_IMAGE_STYLE_PRESETS:
        preset_suffix = GEMINI_IMAGE_STYLE_PRESETS[style]['prompt_suffix'].strip()
        if preset_suffix:
            parts.append(preset_suffix)

    # 4. 比例提示（只有当不使用API参数时才添加到提示词）
    if not use_api_aspect_ratio and aspect_ratio in GEMINI_IMAGE_ASPECT_RATIOS:
        ratio_hint = GEMINI_IMAGE_ASPECT_RATIOS[aspect_ratio]['prompt_hint'].strip()
        if ratio_hint:
            parts.append(ratio_hint)

    # 5. 摘要内容（核心内容，在所有风格之后）
    if base_prompt:
        parts.append(base_prompt.strip())

    # 6. 用户自定义后缀（最后）
    if custom_suffix:
        parts.append(custom_suffix.strip())

    # 使用逗号+空格连接所有部分
    return ', '.join(filter(None, parts)) if parts else base_prompt


def generate_image_with_gemini(
    prompt,
    api_key,
    base_url='https://generativelanguage.googleapis.com',
    model='gemini-2.0-flash-exp',
    style='realistic',
    aspect_ratio='16:9',
    custom_style_prefix='',
    custom_style_suffix='',
    max_retries=3,
    timeout=30
):
    """
    使用 Gemini API 生成图像

    注意：此功能需要使用支持图像生成的 Gemini 模型（如 gemini-2.0-flash-exp）
    或使用支持 Imagen 的代理服务

    Args:
        prompt: 图像描述提示词
        api_key: Gemini API Key
        base_url: API 基础 URL
        model: 使用的模型名称
        style: 预设风格（realistic, illustration, anime, cyberpunk, business等）
        aspect_ratio: 图片比例（1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3）
        custom_style_prefix: 自定义风格前缀
        custom_style_suffix: 自定义风格后缀
        max_retries: 最大重试次数
        timeout: 请求超时时间（秒）

    Returns:
        tuple: (image_path, metadata) 成功时返回图片路径和元数据，失败返回 (None, None)
    """

    # 检查是否将使用 API 参数控制比例
    use_api_aspect_ratio = aspect_ratio and aspect_ratio in GEMINI_IMAGE_ASPECT_RATIOS

    # 应用风格到提示词
    # 如果使用 API 参数控制比例，则不在提示词中重复添加比例描述
    styled_prompt = apply_style_to_prompt(
        prompt,
        style,
        aspect_ratio,
        custom_style_prefix,
        custom_style_suffix,
        use_api_aspect_ratio=use_api_aspect_ratio
    )

    # 构建请求 URL
    if base_url.endswith('/'):
        base_url = base_url[:-1]

    # 尝试多种 API endpoint 格式
    # 1. 使用 generateContent API (Gemini 标准方式)
    # 2. 使用 generateImage API (某些代理可能支持)

    # 首先尝试标准的 generateContent API
    url = f"{base_url}/v1beta/models/{model}:generateContent"

    headers = {
        'Content-Type': 'application/json'
    }

    # 添加 API Key
    if '?' in url:
        url = f"{url}&key={api_key}"
    else:
        url = f"{url}?key={api_key}"

    # 使用 generateContent 格式请求图像生成
    # 根据官方文档：https://ai.google.dev/gemini-api/docs/image-generation
    # aspectRatio 应该放在 generationConfig.imageConfig 中

    generation_config = {
        'temperature': 0.4,
        'topK': 32,
        'topP': 1,
        'maxOutputTokens': 4096,
    }

    # 添加 imageConfig（官方格式）
    aspect_ratio_added = False
    if aspect_ratio and aspect_ratio in GEMINI_IMAGE_ASPECT_RATIOS:
        generation_config['imageConfig'] = {
            'aspectRatio': aspect_ratio
        }
        aspect_ratio_added = True
        print(f"✓ 设置图片比例: {aspect_ratio} (imageConfig)")

    payload = {
        'contents': [{
            'parts': [{
                'text': f'Generate an image: {styled_prompt}'
            }]
        }],
        'generationConfig': generation_config
    }

    retry_count = 0
    last_error = None

    while retry_count < max_retries:
        try:
            print(f"尝试使用 Gemini 生成图像 (第 {retry_count + 1}/{max_retries} 次)...")
            print(f"使用模型: {model}")
            print(f"使用提示词: {styled_prompt[:100]}...")

            # 打印payload结构（用于调试）
            payload_keys = list(payload.keys())
            print(f"Payload 参数: {', '.join(payload_keys)}")
            if 'imageConfig' in payload.get('generationConfig', {}):
                image_config = payload['generationConfig']['imageConfig']
                print(f"  ✓ imageConfig.aspectRatio: {image_config.get('aspectRatio')}")

            response = requests.post(url, headers=headers, json=payload, timeout=timeout)

            # 打印响应以便调试
            print(f"API 响应状态: {response.status_code}")

            # 检查响应状态
            if response.status_code == 200:
                result = response.json()

                # Gemini API 返回的格式通常是 candidates
                if 'candidates' in result:
                    # 检查是否包含 Markdown 格式的图像
                    for candidate in result['candidates']:
                        if 'content' in candidate and 'parts' in candidate['content']:
                            for part in candidate['content']['parts']:
                                if 'text' in part:
                                    text = part['text']
                                    # 检查是否包含 base64 图像数据
                                    # 格式1: Markdown 图片 ![...]（data:image/...;base64,...)
                                    if 'data:image/' in text and 'base64,' in text:
                                        print("✓ 在响应中找到 Markdown 格式的图像数据")
                                        # 提取 base64 数据
                                        import re
                                        # 匹配 data:image/xxx;base64,后面的内容
                                        match = re.search(r'data:image/[^;]+;base64,([^)"\s]+)', text)
                                        if match:
                                            base64_data = match.group(1)
                                            try:
                                                image_bytes = base64.b64decode(base64_data)

                                                # 保存图像
                                                config = load_config()
                                                output_dir = os.path.join(config.get('output_directory', 'output'), 'gemini_images')
                                                os.makedirs(output_dir, exist_ok=True)

                                                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                                                filename = f"gemini_{timestamp}_{uuid.uuid4().hex[:8]}.png"
                                                image_path = os.path.join(output_dir, filename)

                                                with open(image_path, 'wb') as f:
                                                    f.write(image_bytes)

                                                print(f"✓ Gemini 图像生成成功: {image_path}")

                                                # 返回元数据
                                                metadata = {
                                                    'model': model,
                                                    'prompt': styled_prompt,
                                                    'style': style,
                                                    'aspect_ratio': aspect_ratio,
                                                    'timestamp': timestamp,
                                                    'retry_count': retry_count,
                                                    'format': 'markdown_base64'
                                                }

                                                return image_path, metadata
                                            except Exception as e:
                                                print(f"解码 base64 图像失败: {e}")
                                                continue

                    # 如果没有找到 Markdown 格式的图像，继续检查其他格式
                    print(f"警告: 在 candidates 中未找到图像数据")
                    print(f"响应内容: {str(result)[:500]}")
                    last_error = "响应中未包含可识别的图像数据"
                    retry_count += 1
                    continue

                # 尝试提取图像数据（Base64 编码）
                # 支持多种可能的响应格式
                image_data = None
                image_bytes = None

                # 格式1: 直接包含 images 数组
                if 'images' in result and len(result['images']) > 0:
                    image_data = result['images'][0]
                    if 'bytesBase64Encoded' in image_data:
                        image_bytes = base64.b64decode(image_data['bytesBase64Encoded'])
                    elif 'imageData' in image_data:
                        image_bytes = base64.b64decode(image_data['imageData'])
                    elif 'data' in image_data:
                        image_bytes = base64.b64decode(image_data['data'])

                # 格式2: 在 predictions 中
                elif 'predictions' in result and len(result['predictions']) > 0:
                    prediction = result['predictions'][0]
                    if 'bytesBase64Encoded' in prediction:
                        image_bytes = base64.b64decode(prediction['bytesBase64Encoded'])
                    elif 'image' in prediction:
                        image_bytes = base64.b64decode(prediction['image'])

                # 格式3: 直接在根级别
                elif 'image' in result:
                    image_bytes = base64.b64decode(result['image'])
                elif 'bytesBase64Encoded' in result:
                    image_bytes = base64.b64decode(result['bytesBase64Encoded'])

                if image_bytes:
                    # 保存图像
                    config = load_config()
                    output_dir = os.path.join(config.get('output_directory', 'output'), 'gemini_images')
                    os.makedirs(output_dir, exist_ok=True)

                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    filename = f"gemini_{timestamp}_{uuid.uuid4().hex[:8]}.png"
                    image_path = os.path.join(output_dir, filename)

                    with open(image_path, 'wb') as f:
                        f.write(image_bytes)

                    print(f"✓ Gemini 图像生成成功: {image_path}")

                    # 返回元数据
                    metadata = {
                        'model': model,
                        'prompt': styled_prompt,
                        'style': style,
                        'aspect_ratio': aspect_ratio,
                        'timestamp': timestamp,
                        'retry_count': retry_count
                    }

                    return image_path, metadata
                else:
                    print(f"响应中没有找到图像数据")
                    print(f"响应内容: {str(result)[:500]}")
                    last_error = "API 返回成功但未包含图像数据"
                    retry_count += 1
                    continue

            elif response.status_code == 429:
                print(f"API 请求频率限制，等待后重试...")
                last_error = "请求频率超限"
                retry_count += 1
                continue

            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', '未知错误')
                    error_status = error_data.get('error', {}).get('status', '')
                except:
                    error_msg = response.text
                    error_status = ''

                print(f"请求参数错误: {error_msg}")

                # 如果是 INVALID_ARGUMENT 错误且我们添加了 imageConfig，尝试移除后重试
                if 'INVALID_ARGUMENT' in error_status and aspect_ratio_added and retry_count == 0:
                    print(f"⚠️  imageConfig.aspectRatio 参数不被支持，移除后重试...")
                    # 移除 imageConfig
                    if 'imageConfig' in payload.get('generationConfig', {}):
                        del payload['generationConfig']['imageConfig']
                    aspect_ratio_added = False
                    print(f"   将回退到仅使用提示词引导比例")

                    # 重新生成提示词，这次在提示词中包含比例描述
                    styled_prompt = apply_style_to_prompt(
                        prompt,
                        style,
                        aspect_ratio,
                        custom_style_prefix,
                        custom_style_suffix,
                        use_api_aspect_ratio=False  # 不使用API参数，在提示词中添加比例
                    )
                    # 更新 payload 中的提示词
                    payload['contents'][0]['parts'][0]['text'] = f'Generate an image: {styled_prompt}'
                    print(f"   更新提示词包含比例描述: {aspect_ratio}")

                    # 不增加 retry_count，给一次降级重试的机会
                    continue

                last_error = f"请求参数错误: {error_msg}"
                retry_count += 1
                continue

            elif response.status_code == 404:
                try:
                    error_data = response.json()
                    print(f"404 错误详情: {error_data}")

                    # 检查是否是模型不存在的错误
                    error_message = error_data.get('error', {}).get('message', '')
                    if 'not found' in error_message.lower() or 'entity was not found' in error_message.lower():
                        error_msg = f"模型 '{model}' 不存在或不可用。\n\n建议：\n1. 检查模型名称是否正确\n2. 该代理可能不支持此模型，请尝试其他模型\n3. 点击'刷新列表'查看可用模型\n4. 或使用 ComfyUI/图片库 API"
                    else:
                        error_msg = f"API endpoint 不存在: {error_message}"
                except:
                    error_msg = f"API endpoint 不存在（模型: {model}）\n响应: {response.text[:200]}"

                print(f"❌ 404 错误: {error_msg}")
                last_error = error_msg
                # 404 通常意味着配置错误，不需要重试
                break

            else:
                print(f"API 请求失败: {response.status_code} - {response.text[:500]}")
                last_error = f"HTTP {response.status_code}"
                retry_count += 1
                continue

        except requests.exceptions.Timeout:
            print(f"请求超时 (timeout={timeout}s)")
            last_error = "请求超时"
            retry_count += 1
            continue

        except requests.exceptions.ConnectionError as e:
            print(f"连接错误: {e}")
            last_error = f"连接错误: {str(e)}"
            retry_count += 1
            continue

        except Exception as e:
            print(f"生成图像时发生错误: {e}")
            import traceback
            traceback.print_exc()
            last_error = str(e)
            retry_count += 1
            continue

    print(f"✗ Gemini 图像生成失败（已重试 {max_retries} 次）: {last_error}")
    return None, None


def test_gemini_image_api(api_key, base_url, model):
    """
    测试 Gemini 图像生成 API 配置

    Returns:
        tuple: (success: bool, message: str, image_url: str or None)
    """
    try:
        test_prompt = "A beautiful sunset over the ocean"

        image_path, metadata = generate_image_with_gemini(
            prompt=test_prompt,
            api_key=api_key,
            base_url=base_url,
            model=model,
            style='realistic',
            aspect_ratio='16:9',  # 测试时使用16:9比例
            max_retries=3,  # 设置重试次数：第1次尝试imageConfig，失败后降级重试，最多3次
            timeout=30
        )

        if image_path:
            # 测试成功，返回成功信息
            aspect_info = metadata.get('aspect_ratio', '未知')
            return True, f'Gemini 图像生成 API 工作正常 (比例: {aspect_info})', image_path
        else:
            return False, 'API 测试失败，请检查配置和模型是否支持图像生成', None

    except Exception as e:
        error_msg = str(e)
        # 提供更详细的错误信息
        if 'INVALID_ARGUMENT' in error_msg:
            return False, f'参数错误: 模型可能不支持图像生成或配置有误\n{error_msg}', None
        elif '401' in error_msg or 'Unauthorized' in error_msg:
            return False, f'API Key 验证失败: 请检查 API Key 是否正确\n{error_msg}', None
        elif '404' in error_msg:
            return False, f'模型不存在: 请检查模型名称是否正确\n{error_msg}', None
        else:
            return False, f'测试失败: {error_msg}', None


def get_gemini_image_models(api_key, base_url='https://generativelanguage.googleapis.com'):
    """
    从 Gemini API 获取可用的图像生成模型列表

    Returns:
        list: 模型列表
    """
    try:
        # 构建请求 URL
        if base_url.endswith('/'):
            base_url = base_url[:-1]

        # 尝试获取模型列表
        url = f"{base_url}/v1beta/models?key={api_key}"

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        result = response.json()

        # 收集所有模型
        all_models = []
        if 'models' in result:
            for model in result['models']:
                model_name = model.get('name', '').replace('models/', '')
                display_name = model.get('displayName', model_name)
                description = model.get('description', '')

                # 检查模型支持的方法
                supported_methods = model.get('supportedGenerationMethods', [])

                # 优先选择支持图像生成的模型
                # 注意：当前 Gemini 模型主要支持文本生成，图像生成可能需要特殊模型或代理
                is_image_model = (
                    'imagen' in model_name.lower() or
                    'image' in model_name.lower() or
                    'generateImage' in supported_methods or
                    'vision' in model_name.lower()
                )

                # 优化显示名称，添加更多区分信息
                enhanced_name = display_name

                # 如果是 Nano Banana / Gemini Image 模型，添加版本标识
                if 'image' in model_name.lower():
                    # 提取版本信息
                    if '2.5' in model_name:
                        if 'preview' in model_name.lower():
                            enhanced_name = f"{display_name} (v2.5 预览版)"
                        else:
                            enhanced_name = f"{display_name} (v2.5)"
                    elif '2.0' in model_name:
                        enhanced_name = f"{display_name} (v2.0)"
                    elif 'preview' in model_name.lower():
                        enhanced_name = f"{display_name} (预览版)"

                # 如果名称中包含 "Nano Banana"，添加推荐标识
                if 'nano' in display_name.lower() or 'banana' in display_name.lower():
                    if not any(tag in enhanced_name for tag in ['推荐', '预览版', 'v2.']):
                        enhanced_name = f"{enhanced_name} [推荐]"

                all_models.append({
                    'id': model_name,
                    'name': enhanced_name,
                    'description': description,
                    'is_image_model': is_image_model,
                    'supported_methods': supported_methods
                })

        # 按优先级排序：图像模型优先
        all_models.sort(key=lambda x: (not x['is_image_model'], x['name']))

        # 如果没有找到模型，返回推荐的默认模型列表
        if not all_models:
            return [
                {
                    'id': 'gemini-2.0-flash-exp',
                    'name': 'Gemini 2.0 Flash (实验版)',
                    'description': '支持多模态的最新实验模型，可能支持图像生成'
                },
                {
                    'id': 'gemini-1.5-pro',
                    'name': 'Gemini 1.5 Pro',
                    'description': 'Pro 版本，功能更强大'
                },
                {
                    'id': 'gemini-1.5-flash',
                    'name': 'Gemini 1.5 Flash',
                    'description': '快速响应版本'
                }
            ]

        # 返回前 10 个模型
        return [
            {
                'id': m['id'],
                'name': m['name'],
                'description': m['description'] or '无描述'
            }
            for m in all_models[:10]
        ]

    except Exception as e:
        print(f"获取 Gemini 模型列表失败: {e}")
        import traceback
        traceback.print_exc()

        # 返回推荐的默认模型
        return [
            {
                'id': 'gemini-2.0-flash-exp',
                'name': 'Gemini 2.0 Flash (实验版)',
                'description': '推荐：支持多模态的最新实验模型'
            },
            {
                'id': 'gemini-1.5-pro',
                'name': 'Gemini 1.5 Pro',
                'description': 'Pro 版本，功能更强大'
            },
            {
                'id': 'gemini-1.5-flash',
                'name': 'Gemini 1.5 Flash',
                'description': '快速响应版本'
            }
        ]
