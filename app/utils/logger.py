"""日志配置模块"""

import logging
import sys

# 创建日志格式器
class SimpleFormatter(logging.Formatter):
    """简洁的日志格式器"""

    FORMATS = {
        logging.DEBUG: "🔍 %(message)s",
        logging.INFO: "ℹ️  %(message)s",
        logging.WARNING: "⚠️  %(message)s",
        logging.ERROR: "❌ %(message)s",
        logging.CRITICAL: "🔥 %(message)s",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, "%(message)s")
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logger(name='app', level=logging.INFO):
    """
    配置日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）

    Returns:
        logger: 配置好的日志记录器
    """
    logger = logging.getLogger(name)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(SimpleFormatter())

    logger.addHandler(console_handler)

    return logger


# 创建默认日志记录器
default_logger = setup_logger('app', logging.INFO)


def log_info(message):
    """输出信息日志"""
    default_logger.info(message)


def log_debug(message):
    """输出调试日志"""
    default_logger.debug(message)


def log_warning(message):
    """输出警告日志"""
    default_logger.warning(message)


def log_error(message):
    """输出错误日志"""
    default_logger.error(message)
