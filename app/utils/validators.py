"""输入验证相关的工具函数"""

from app.config import IMAGE_STYLE_TEMPLATES


def validate_image_count(count):
    """验证图片数量是否有效"""
    return count in (1, 3)


def validate_style_template(template_id):
    """验证风格模板ID是否有效"""
    return template_id in IMAGE_STYLE_TEMPLATES


def normalize_field(value, fallback):
    """标准化字段值，空值时使用回退值"""
    if not value:
        return fallback
    return str(value).strip()
