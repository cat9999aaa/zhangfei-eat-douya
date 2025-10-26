/**
 * 工具函数库
 */

const Utils = {
    /**
     * 防抖函数
     * @param {Function} func - 要防抖的函数
     * @param {number} wait - 等待时间（毫秒）
     */
    debounce(func, wait = 300) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * 节流函数
     * @param {Function} func - 要节流的函数
     * @param {number} limit - 时间限制（毫秒）
     */
    throttle(func, limit = 300) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * 格式化文件大小
     * @param {number} bytes - 字节数
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    },

    /**
     * 格式化日期
     * @param {Date|string} date - 日期对象或字符串
     * @param {string} format - 格式模板
     */
    formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
        const d = new Date(date);
        if (isNaN(d.getTime())) return '';

        const pad = (n) => String(n).padStart(2, '0');

        const replacements = {
            'YYYY': d.getFullYear(),
            'MM': pad(d.getMonth() + 1),
            'DD': pad(d.getDate()),
            'HH': pad(d.getHours()),
            'mm': pad(d.getMinutes()),
            'ss': pad(d.getSeconds())
        };

        let result = format;
        for (const [key, value] of Object.entries(replacements)) {
            result = result.replace(key, value);
        }
        return result;
    },

    /**
     * 相对时间（多久之前）
     * @param {Date|string} date - 日期
     */
    timeAgo(date) {
        const d = new Date(date);
        const now = new Date();
        const seconds = Math.floor((now - d) / 1000);

        if (seconds < 60) return '刚刚';
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes}分钟前`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}小时前`;
        const days = Math.floor(hours / 24);
        if (days < 30) return `${days}天前`;
        const months = Math.floor(days / 30);
        if (months < 12) return `${months}个月前`;
        const years = Math.floor(months / 12);
        return `${years}年前`;
    },

    /**
     * 复制文本到剪贴板
     * @param {string} text - 要复制的文本
     */
    async copyToClipboard(text) {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(text);
            return true;
        } else {
            // 降级方案
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                return true;
            } catch (err) {
                console.error('复制失败:', err);
                return false;
            } finally {
                document.body.removeChild(textArea);
            }
        }
    },

    /**
     * 验证URL
     * @param {string} url - URL字符串
     */
    isValidURL(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    },

    /**
     * 验证邮箱
     * @param {string} email - 邮箱地址
     */
    isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    /**
     * 生成随机ID
     * @param {number} length - ID长度
     */
    generateId(length = 8) {
        return Math.random().toString(36).substring(2, 2 + length);
    },

    /**
     * 延迟执行
     * @param {number} ms - 延迟时间（毫秒）
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },

    /**
     * 数组分块
     * @param {Array} array - 原数组
     * @param {number} size - 每块大小
     */
    chunk(array, size) {
        const chunks = [];
        for (let i = 0; i < array.length; i += size) {
            chunks.push(array.slice(i, i + size));
        }
        return chunks;
    },

    /**
     * 去重
     * @param {Array} array - 原数组
     */
    unique(array) {
        return [...new Set(array)];
    },

    /**
     * 深度克隆
     * @param {*} obj - 要克隆的对象
     */
    deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => this.deepClone(item));
        if (obj instanceof Object) {
            const clonedObj = {};
            for (const key in obj) {
                if (obj.hasOwnProperty(key)) {
                    clonedObj[key] = this.deepClone(obj[key]);
                }
            }
            return clonedObj;
        }
    },

    /**
     * 对象是否为空
     * @param {Object} obj - 对象
     */
    isEmpty(obj) {
        if (obj == null) return true;
        if (Array.isArray(obj) || typeof obj === 'string') return obj.length === 0;
        return Object.keys(obj).length === 0;
    },

    /**
     * 安全的JSON解析
     * @param {string} str - JSON字符串
     * @param {*} defaultValue - 默认值
     */
    safeJSONParse(str, defaultValue = null) {
        try {
            return JSON.parse(str);
        } catch {
            return defaultValue;
        }
    },

    /**
     * 滚动到元素
     * @param {HTMLElement|string} element - 元素或选择器
     * @param {string} behavior - 滚动行为: smooth, auto
     */
    scrollToElement(element, behavior = 'smooth') {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (el) {
            el.scrollIntoView({ behavior, block: 'start' });
        }
    },

    /**
     * 获取URL参数
     * @param {string} name - 参数名
     */
    getQueryParam(name) {
        const params = new URLSearchParams(window.location.search);
        return params.get(name);
    },

    /**
     * 设置URL参数
     * @param {string} name - 参数名
     * @param {string} value - 参数值
     */
    setQueryParam(name, value) {
        const url = new URL(window.location);
        url.searchParams.set(name, value);
        window.history.pushState({}, '', url);
    },

    /**
     * 下载文件
     * @param {string} url - 文件URL
     * @param {string} filename - 文件名
     */
    downloadFile(url, filename) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename || '';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },

    /**
     * 控制模态框打开时的滚动锁定
     * @param {boolean} lock - 是否锁定滚动
     */
    toggleModalScrollLock(lock) {
        const className = 'write-modal-locked';
        if (lock) {
            document.body.classList.add(className);
            return;
        }
        const hasVisibleModal = document.querySelector('.write-modal[aria-hidden=\"false\"]');
        if (!hasVisibleModal) {
            document.body.classList.remove(className);
        }
    },

    /**
     * 全屏切换
     */
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        } else if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    },

    /**
     * 检测暗色模式
     */
    isDarkMode() {
        return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    },

    /**
     * 触觉反馈（移动设备）
     */
    hapticFeedback(type = 'medium') {
        if ('vibrate' in navigator) {
            const patterns = {
                light: 10,
                medium: 20,
                heavy: 30
            };
            navigator.vibrate(patterns[type] || patterns.medium);
        }
    }
};

// 暴露到全局
window.Utils = Utils;

// 也可以作为模块导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Utils;
}
