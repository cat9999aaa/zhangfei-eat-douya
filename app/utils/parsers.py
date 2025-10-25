"""JSON和文本解析工具"""

import re
import json


def strip_json_text(text):
    """去除 ```json 代码块等包装"""
    cleaned = text.strip()
    if cleaned.startswith('```'):
        cleaned = re.sub(r'^```[a-zA-Z]*\n', '', cleaned)
        cleaned = re.sub(r'\n```$', '', cleaned)
    return cleaned.strip()


def parse_json_response(text):
    """尽量从模型响应中解析 JSON"""
    cleaned = strip_json_text(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', cleaned, re.S)
        if match:
            snippet = match.group(0)
            try:
                return json.loads(snippet)
            except json.JSONDecodeError:
                pass
    raise ValueError('无法解析模型返回的 JSON')


def extract_article_title(article):
    """从文章内容中提取标题（第一行或第一段）"""
    lines = article.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line:
            # 去除 Markdown 标记
            title = re.sub(r'^#+\s*', '', line)
            title = re.sub(r'\*\*(.*?)\*\*', r'\1', title)
            title = re.sub(r'\*(.*?)\*', r'\1', title)
            return title.strip()
    return "未命名文章"


def derive_keyword_from_blueprint(blueprint):
    """从视觉蓝图中提取英文关键词，用于备用图片源"""
    if not blueprint:
        return ''
    text = ' '.join([
        str(blueprint.get('subject', '')),
        str(blueprint.get('scene', '')),
        str(blueprint.get('details', ''))
    ])
    words = re.findall(r'[A-Za-z]+', text)
    if not words:
        return ''
    return ' '.join(words[:4]).lower()
