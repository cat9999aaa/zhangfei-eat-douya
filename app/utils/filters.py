"""
文本内容过滤器模块 (最终架构版 v4 - 实时关键词)
集成了 GFWList 黑名单、TLD 白名单、静态链接检测、实时关键词黑名单、
以及由多个 OpenCC 引擎驱动的最高精度繁体中文过滤系统。
"""
import re
from urllib.parse import urlparse
import os
import datetime
import opencc

# --- 1. 初始化与配置 ---
# OpenCC 多引擎
OPENCC_CONVERTERS = []
try:
    configs = ['t2s', 'tw2s', 'hk2s']
    for config in configs:
        OPENCC_CONVERTERS.append(opencc.OpenCC(config))
    OPENCC_AVAILABLE = True
    print(f"✓ OpenCC 多引擎繁体检测系统 ({len(OPENCC_CONVERTERS)}个引擎) 加载成功。")
except Exception as e:
    OPENCC_CONVERTERS = []
    OPENCC_AVAILABLE = False
    print(f"⚠️ 警告: OpenCC 加载失败 ({e})。")

# 路径配置
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
GFWLIST_DIR = os.path.join(BASE_DIR, 'gfwlist')
BLACKLIST_FILE = os.path.join(GFWLIST_DIR, 'list.txt')
TEXT_BLACKLIST_FILE = os.path.join(GFWLIST_DIR, 'text_list.txt')
LOG_DIR = os.path.join(GFWLIST_DIR, 'logs')

# 状态变量 (仅用于需要缓存的大文件)
BLACKLISTED_DOMAINS = set()
GFWLIST_LOADED = False
LOG_FILE_PATH = None

# TLD 白名单 和 静态文件后缀
ALLOWED_TLDS = {'.com', '.cn', '.org', '.com.cn', '.gov', '.gov.cn', '.net'}
STATIC_EXTENSIONS = {'.html', '.htm'}


# --- 2. 内容与格式审查 ---
def contains_chinese(text):
    if not text: return False
    return bool(re.search(r'[\u4e00-\u9fa5]', text))

def contains_traditional_chinese(text):
    if not text or not OPENCC_AVAILABLE: return False
    for converter in OPENCC_CONVERTERS:
        if converter.convert(text) != text:
            return True
    return False

def is_static_url(url):
    try:
        path = urlparse(url).path
        return any(path.lower().endswith(ext) for ext in STATIC_EXTENSIONS)
    except Exception:
        return False

def contains_blacklisted_keyword(text):
    """
    动态检查：每次调用都重新读取 text_list.txt，确保规则实时生效。
    """
    if not text:
        return False
    try:
        # 每次都重新打开并读取文件，确保实时性
        with open(TEXT_BLACKLIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                keyword = line.strip()
                # 确保关键词非空且不是注释，然后检查是否在文本中
                if keyword and not keyword.startswith('!') and keyword in text:
                    return True # 只要找到一个匹配就立即返回
        return False # 遍历完文件都未找到
    except FileNotFoundError:
        # 只有在第一次找不到文件时打印警告，避免刷屏
        if not hasattr(contains_blacklisted_keyword, 'warned_not_found'):
            print(f"⚠️ 警告: 关键词黑名单 {TEXT_BLACKLIST_FILE} 未找到，该过滤规则将跳过。")
            contains_blacklisted_keyword.warned_not_found = True
        return False
    except Exception as e:
        # 只有在第一次发生读取错误时打印警告
        if not hasattr(contains_blacklisted_keyword, 'warned_error'):
            print(f"❌ 读取关键词黑名单时发生错误: {e}")
            contains_blacklisted_keyword.warned_error = True
        return False

# --- 3. 黑名单与白名单加载与检查 ---
def is_tld_whitelisted(url):
    try:
        domain = urlparse(url).netloc
        if not domain: return False
        return any(domain.endswith(tld) for tld in ALLOWED_TLDS)
    except Exception:
        return False

def load_gfwlist_blacklist():
    global BLACKLISTED_DOMAINS, GFWLIST_LOADED
    if GFWLIST_LOADED: return
    print(f"🔌 正在加载 GFWList 域名黑名单: {BLACKLIST_FILE}")
    try:
        with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('!') and not line.startswith('['):
                    domain = ''
                    if line.startswith('||'): domain = re.sub(r'[/^*].*$', '', line[2:])
                    elif line.startswith('|http'):
                        try: domain = urlparse(line[1:]).netloc
                        except Exception: continue
                    else: domain = re.sub(r'[/^*].*$', '', re.sub(r'^[.@]*', '', line))
                    if domain and '.' in domain: BLACKLISTED_DOMAINS.add(domain)
        GFWLIST_LOADED = True
        print(f"✓ GFWList 加载成功，共 {len(BLACKLISTED_DOMAINS)} 条规则。")
    except FileNotFoundError:
        print(f"⚠️ 警告: GFWList 黑名单文件 {BLACKLIST_FILE} 未找到。")
    except Exception as e:
        print(f"❌ 加载 GFWList 时发生错误: {e}")

def is_domain_blacklisted(url):
    if not GFWLIST_LOADED: load_gfwlist_blacklist()
    if not url or not BLACKLISTED_DOMAINS: return None
    try:
        domain = urlparse(url).netloc
        if not domain: return None
        parts = domain.split('.')
        for i in range(len(parts)):
            sub_domain = '.'.join(parts[i:])
            if sub_domain in BLACKLISTED_DOMAINS:
                return sub_domain
        return None
    except Exception:
        return None

# --- 4. 日志 ---
def _get_log_file_path():
    global LOG_FILE_PATH
    if LOG_FILE_PATH: return LOG_FILE_PATH
    os.makedirs(LOG_DIR, exist_ok=True)
    date_str = datetime.datetime.now().strftime('%Y_%m_%d')
    sequence = 1
    while True:
        filename = f"{date_str}_{sequence:02d}_gfw_logs.txt"
        path = os.path.join(LOG_DIR, filename)
        if not os.path.exists(path):
            LOG_FILE_PATH = path
            return path
        sequence += 1

def log_filtered_event(url, reason, detail):
    try:
        log_path = _get_log_file_path()
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] Blocked URL: {url} | Reason: {reason} | Detail: {detail}\n"
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(log_message)
    except Exception as e:
        print(f"❌ 写入过滤日志时发生错误: {e}")
