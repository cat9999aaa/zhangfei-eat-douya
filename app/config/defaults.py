"""默认配置常量"""

# 允许的图片文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}

# 默认的 ComfyUI 配置
DEFAULT_COMFYUI_CONFIG = {
    'enabled': True,
    'server_url': 'http://127.0.0.1:8188',
    'queue_size': 2,
    'timeout_seconds': 180,
    'max_attempts': 2,
    'seed': -1,
    'workflow_path': ''
}

# 预设的视觉模板，用于构建提示词
VISUAL_TEMPLATE_PRESETS = {
    'portrait': {
        'name': '人物特写',
        'positive_prefix': 'ultra detailed cinematic portrait of',
        'positive_suffix': 'sharp focus, 8k, masterpiece, award-winning photography, intricate details, volumetric lighting, high dynamic range',
        'negative': 'lowres, blurry, worst quality, low quality, jpeg artifacts, double face, deformed, cropped, watermark, nsfw'
    },
    'urban_story': {
        'name': '城市纪实',
        'positive_prefix': 'documentary style wide shot of',
        'positive_suffix': 'cinematic storytelling, atmospheric haze, dramatic lighting, realistic photography, depth of field, editorial style, moody ambience',
        'negative': 'lowres, cartoon, painting, illustration, abstract, blurry, distorted, watermark'
    },
    'technology': {
        'name': '科技概念',
        'positive_prefix': 'futuristic concept art of',
        'positive_suffix': 'highly detailed, sleek design, glows, holographic interface, volumetric light, digital art, 8k render, cinematic lighting',
        'negative': 'lowres, blurry, noisy, childlike, hand-drawn, distorted, watermark'
    },
    'nature': {
        'name': '自然风光',
        'positive_prefix': 'breathtaking landscape of',
        'positive_suffix': 'golden hour lighting, ultra realistic, depth of field, atmospheric perspective, highly detailed, award-winning photography',
        'negative': 'lowres, oversaturated, blurry, distorted, extra limbs, watermark, cartoon'
    },
    'editorial': {
        'name': '资讯配图',
        'positive_prefix': 'editorial style illustration of',
        'positive_suffix': 'clean composition, modern infographic aesthetics, vector inspired, balanced color palette, professional magazine layout, sharp details',
        'negative': 'lowres, childish drawing, messy typography, watermark, depressing filter, distorted text'
    },
    'abstract': {
        'name': '抽象概念',
        'positive_prefix': 'abstract conceptual illustration of',
        'positive_suffix': 'minimalist shapes, clean vector art, modern gradients, smooth lighting, design magazine aesthetic, crisp edges, high resolution',
        'negative': 'lowres, messy composition, noisy texture, random clutter, illegible text, watermark'
    }
}

# 图片风格模板
IMAGE_STYLE_TEMPLATES = {
    'custom': {
        'label': '自定义风格',
        'positive': '',
        'negative': ''
    },
    'realistic_photo': {
        'label': '写实摄影',
        'positive': 'highly detailed realistic photography, natural lighting, sharp focus',
        'negative': 'cartoon, illustration, painting, lowres, oversaturated, cgi'
    },
    'cyberpunk': {
        'label': '赛博朋克',
        'positive': 'cyberpunk, neon rain, dramatic lighting, futuristic cityscape',
        'negative': 'lowres, watercolor, sketch, plain background'
    },
    'business': {
        'label': '商务插画',
        'positive': 'business illustration, clean vector style, professional tone, modern minimal branding',
        'negative': 'messy, chaotic, childish, graffiti'
    }
}

# Gemini 图像生成配置
DEFAULT_GEMINI_IMAGE_CONFIG = {
    'enabled': False,  # 默认禁用，需要用户配置后启用
    'api_key': '',  # 可以与文本生成共用，也可以单独配置
    'base_url': 'https://generativelanguage.googleapis.com',
    'model': 'gemini-2.0-flash-exp',  # 推荐使用最新的实验模型
    'style': 'realistic',  # 默认风格
    'custom_prefix': '',  # 自定义提示词前缀
    'custom_suffix': '',  # 自定义提示词后缀
    'max_retries': 3,  # 默认重试 3 次
    'timeout': 30,  # 超时时间（秒）
    'aspect_ratio': '16:9'  # 默认宽高比
}

# 摘要模型选项
SUMMARY_MODEL_SPECIAL_OPTIONS = ['__default__']

# 配置文件路径
CONFIG_FILE = 'config.json'
