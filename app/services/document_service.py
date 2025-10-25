"""文档生成服务模块"""

import os
import re
import subprocess
from app.utils.file_helpers import sanitize_title
from app.config.loader import load_config


def extract_paragraph_structures(markdown_text):
    """从Markdown文章中提取段落结构"""
    lines = markdown_text.split('\n')
    paragraphs = []
    current_para = []
    start_line = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

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

    return paragraphs


def compute_image_slots(paragraphs, target_count):
    """计算图片插入位置

    策略：
    - 避免图片放在文章最后一段之后
    - 尽量均匀分布
    - 段落不足时智能处理
    """
    if not paragraphs:
        return [None] * target_count

    para_count = len(paragraphs)

    if para_count == 1:
        return [0] * target_count

    if para_count == 2:
        if target_count == 1:
            return [0]
        elif target_count == 2:
            return [0, 1]
        else:  # target_count == 3
            return [0, 0, 1]

    # 3段及以上的情况
    if para_count < target_count:
        slots = list(range(para_count - 1))
        remaining = target_count - (para_count - 1)
        for i in range(remaining):
            insert_pos = min(para_count - 2, (para_count - 2) // 2)
            slots.append(insert_pos)
        return sorted(slots)

    # 段落足够，均匀分布
    if target_count == 1:
        return [0]
    elif target_count == 3:
        if para_count == 3:
            return [0, 1, 1]
        else:
            middle = para_count // 2
            last_pos = para_count - 2
            return [0, middle, last_pos]
    else:
        step = (para_count - 1) / target_count
        return [min(int(i * step), para_count - 2) for i in range(target_count)]


def inject_images_into_markdown(markdown_text, image_list):
    """将多张图片按指定位置插入到Markdown文章中

    Args:
        markdown_text: 原始Markdown文本
        image_list: 图片列表，每项包含 {'path', 'summary', 'paragraph_index'}
    Returns:
        处理后的Markdown文本
    """
    if not image_list:
        return markdown_text

    lines = markdown_text.split('\n')
    paragraphs = extract_paragraph_structures(markdown_text)

    insertions = {}
    end_insertions = []

    for img_info in image_list:
        para_idx = img_info.get('paragraph_index')
        img_path = img_info.get('path', '')
        img_alt = ""

        if para_idx is None:
            end_insertions.append(f"![{img_alt}]({img_path})")
        elif 0 <= para_idx < len(paragraphs):
            para = paragraphs[para_idx]
            insert_line = para['end_line'] + 1
            if insert_line not in insertions:
                insertions[insert_line] = []
            insertions[insert_line].append(f"![{img_alt}]({img_path})")

    # 从后向前插入，避免索引变化
    for line_idx in sorted(insertions.keys(), reverse=True):
        insert_content = insertions[line_idx]
        for img_md in reversed(insert_content):
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
