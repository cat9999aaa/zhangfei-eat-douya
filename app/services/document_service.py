"""文档生成服务模块"""

import os
import re
import subprocess
from app.utils.file_helpers import sanitize_title
from app.config.loader import load_config


def extract_paragraph_structures(markdown_text):
    """从Markdown文章中提取段落结构和小标题位置"""
    lines = markdown_text.split('\n')
    paragraphs = []
    headings = []  # 记录所有小标题（## 开头）的位置
    current_para = []
    start_line = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        # 记录小标题位置（## 开头的是小标题，# 是主标题）
        if stripped.startswith('## '):
            headings.append({
                'line': i,
                'text': stripped
            })

        # 跳过空行和标题行
        if not stripped or stripped.startswith('#'):
            if current_para:
                paragraphs.append({
                    'text': '\n'.join(current_para),
                    'start_line': start_line,
                    'end_line': i - 1
                })
                current_para = []
            continue

        # 开始新段落
        if not current_para:
            start_line = i
        current_para.append(line)

    # 保存最后一个段落
    if current_para:
        paragraphs.append({
            'text': '\n'.join(current_para),
            'start_line': start_line,
            'end_line': len(lines) - 1
        })

    return paragraphs, headings


def compute_image_slots(paragraphs, target_count, headings=None):
    """计算图片插入位置

    新策略：
    - 优先插入到小标题（## 开头）之后
    - 第一张图：如果有小标题，插到第一个小标题后；没有小标题，插到主标题（#）后
    - 后续图片：均匀分配到各个小标题后
    - 避免图片插在文章开头（主标题之前）
    - 避免图片放在最后一段之后

    Args:
        paragraphs: 段落列表
        target_count: 目标图片数量
        headings: 小标题列表（包含行号）

    Returns:
        list: 图片插入的段落索引列表（注意：现在返回的是行号，不是段落索引）
    """
    if not paragraphs:
        return [None] * target_count

    # 如果没有小标题信息，使用旧逻辑（向后兼容）
    if headings is None:
        para_count = len(paragraphs)
        if para_count == 1:
            return [0] * target_count
        step = max(1, para_count // target_count)
        return [min(i * step, para_count - 2) for i in range(target_count)]

    # 新逻辑：基于小标题插入
    if not headings:
        # 没有小标题，第一张图插到主标题后（段落0），其余均匀分布
        if not paragraphs:
            return [None] * target_count
        if target_count == 1:
            return [0]
        para_count = len(paragraphs)
        step = max(1, (para_count - 1) // target_count)
        return [min(i * step, para_count - 2) for i in range(target_count)]

    # 有小标题：优先分配到小标题后
    slots = []
    heading_count = len(headings)

    if target_count <= heading_count:
        # 图片数量 <= 小标题数量：均匀选择小标题
        step = heading_count / target_count
        for i in range(target_count):
            heading_idx = min(int(i * step), heading_count - 1)
            slots.append(headings[heading_idx]['line'])
    else:
        # 图片数量 > 小标题数量：每个小标题后至少一张，剩余的均匀分配
        # 先在每个小标题后插入一张
        for heading in headings:
            slots.append(heading['line'])

        # 剩余的图片均匀分配
        remaining = target_count - heading_count
        if remaining > 0 and heading_count > 1:
            # 在小标题之间插入剩余图片
            for i in range(remaining):
                # 找到最稀疏的区间
                heading_idx = (i * heading_count) // remaining
                if heading_idx < len(headings):
                    slots.append(headings[heading_idx]['line'])

    # 排序并返回
    return sorted(slots[:target_count])


def inject_images_into_markdown(markdown_text, image_list):
    """将多张图片按指定位置插入到Markdown文章中

    新策略：图片插入到小标题之后，而不是段落结尾

    Args:
        markdown_text: 原始Markdown文本
        image_list: 图片列表，每项包含 {'path', 'summary', 'insert_line'}
                   insert_line 是插入位置的行号
    Returns:
        处理后的Markdown文本
    """
    if not image_list:
        return markdown_text

    lines = markdown_text.split('\n')
    insertions = {}
    end_insertions = []

    for img_info in image_list:
        insert_line = img_info.get('insert_line')
        img_path = img_info.get('path', '')
        img_alt = ""

        if insert_line is None:
            end_insertions.append(f"![{img_alt}]({img_path})")
        else:
            # 插入位置：小标题行号 + 1（紧跟小标题）
            target_line = insert_line + 1
            if target_line not in insertions:
                insertions[target_line] = []
            insertions[target_line].append(f"![{img_alt}]({img_path})")

    # 从后向前插入，避免索引变化
    for line_idx in sorted(insertions.keys(), reverse=True):
        insert_content = insertions[line_idx]
        for img_md in reversed(insert_content):
            # 插入空行和图片
            lines.insert(line_idx, '')
            lines.insert(line_idx, img_md)
            lines.insert(line_idx, '')

    # 文末插入
    if end_insertions:
        lines.append('')
        for img_md in end_insertions:
            lines.append('')
            lines.append(img_md)
            lines.append('')

    return '\n'.join(lines)


def add_no_image_warning(content):
    """在第一段后添加配图提示"""
    lines = content.split('\n')
    processed_content = []
    first_paragraph_found = False

    for line in lines:
        line_stripped = line.strip()
        processed_content.append(line)

        if not first_paragraph_found and line_stripped and not line_stripped.startswith('#'):
            first_paragraph_found = True
            processed_content.append('')
            processed_content.append('**<span style="color:red;">请自行配图！！</span>**')
            processed_content.append('')

    return '\n'.join(processed_content)


def create_word_document(title, content, image_list=None, enable_image=True, pandoc_path='pandoc', config=None):
    """使用 pandoc 将 Markdown 转换为 Word 文档

    Args:
        title: 文章标题
        content: Markdown内容
        image_list: 图片列表，每项包含 {'path', 'summary', 'paragraph_index'}
        enable_image: 是否启用图片
        pandoc_path: Pandoc可执行文件路径
        config: 配置对象(可选)
    """
    # 生成文件名
    safe_title = sanitize_title(title)
    filename = f'{safe_title}.docx'

    # 获取输出目录
    if not config:
        config = load_config()
    output_dir = config.get('output_directory', 'output')
    os.makedirs(output_dir, exist_ok=True)

    filepath = os.path.join(output_dir, filename)

    # 处理图片插入
    if enable_image and image_list:
        # 兼容旧格式
        if isinstance(image_list, str):
            if os.path.exists(image_list):
                image_list = [{
                    'path': image_list,
                    'summary': '配图',
                    'paragraph_index': 0
                }]
            else:
                image_list = []

        if image_list:
            processed_content = inject_images_into_markdown(content, image_list)
        else:
            processed_content = add_no_image_warning(content)
    elif enable_image:
        processed_content = add_no_image_warning(content)
    else:
        processed_content = content

    # 保存 Markdown 文件
    md_filepath = filepath.replace('.docx', '.md')
    with open(md_filepath, 'w', encoding='utf-8') as f:
        f.write(processed_content)

    try:
        # 使用 pandoc 转换为 Word
        cmd = [
            pandoc_path,
            md_filepath,
            '-o', filepath,
            '--standalone'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            raise Exception(f'Pandoc 转换失败: {result.stderr}')

        # 删除临时 Markdown 文件
        try:
            os.remove(md_filepath)
        except:
            pass

        # 删除临时图片文件
        if image_list and isinstance(image_list, list):
            for img_info in image_list:
                img_path = img_info.get('path', '')
                if img_path and 'temp_' in os.path.basename(img_path) and os.path.exists(img_path):
                    try:
                        os.remove(img_path)
                    except:
                        pass

        return filename

    except FileNotFoundError:
        raise Exception(f'找不到 Pandoc，请检查路径配置: {pandoc_path}')
    except subprocess.TimeoutExpired:
        raise Exception('Pandoc 转换超时')
    except Exception as e:
        # 删除临时文件
        try:
            os.remove(md_filepath)
        except:
            pass
        raise e


def list_generated_documents(config):
    """获取已生成的文档列表"""
    from datetime import datetime

    output_dir = config.get('output_directory', 'output')
    files = []

    if os.path.exists(output_dir):
        for filename in os.listdir(output_dir):
            if filename.endswith('.docx') and not filename.startswith('~'):
                filepath = os.path.join(output_dir, filename)
                stats = os.stat(filepath)
                title = filename.replace('.docx', '')
                files.append({
                    'filename': filename,
                    'size': stats.st_size,
                    'created': datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    'title': title
                })

    # 按创建时间倒序排列
    files.sort(key=lambda x: x['created'], reverse=True)
    return files
