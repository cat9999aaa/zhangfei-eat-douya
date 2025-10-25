/**
 * LocalStorage 管理
 * 提供类型安全的本地存储操作
 */

class Storage {
    constructor(prefix = 'zfcdy_') {
        this.prefix = prefix;
    }

    /**
     * 生成完整的key
     */
    getKey(key) {
        return this.prefix + key;
    }

    /**
     * 设置值
     * @param {string} key - 键名
     * @param {*} value - 值（会自动JSON化）
     * @param {number} ttl - 过期时间（毫秒），0表示永不过期
     */
    set(key, value, ttl = 0) {
        try {
            const fullKey = this.getKey(key);
            const data = {
                value,
                timestamp: Date.now(),
                ttl
            };
            localStorage.setItem(fullKey, JSON.stringify(data));
            return true;
        } catch (error) {
            console.error('Storage set error:', error);
            return false;
        }
    }

    /**
     * 获取值
     * @param {string} key - 键名
     * @param {*} defaultValue - 默认值
     */
    get(key, defaultValue = null) {
        try {
            const fullKey = this.getKey(key);
            const item = localStorage.getItem(fullKey);

            if (!item) return defaultValue;

            const data = JSON.parse(item);

            // 检查是否过期
            if (data.ttl > 0) {
                const now = Date.now();
                if (now - data.timestamp > data.ttl) {
                    this.remove(key);
                    return defaultValue;
                }
            }

            return data.value;
        } catch (error) {
            console.error('Storage get error:', error);
            return defaultValue;
        }
    }

    /**
     * 删除值
     * @param {string} key - 键名
     */
    remove(key) {
        try {
            const fullKey = this.getKey(key);
            localStorage.removeItem(fullKey);
            return true;
        } catch (error) {
            console.error('Storage remove error:', error);
            return false;
        }
    }

    /**
     * 清空所有值（仅清空带前缀的）
     */
    clear() {
        try {
            const keys = Object.keys(localStorage);
            keys.forEach(key => {
                if (key.startsWith(this.prefix)) {
                    localStorage.removeItem(key);
                }
            });
            return true;
        } catch (error) {
            console.error('Storage clear error:', error);
            return false;
        }
    }

    /**
     * 检查key是否存在
     * @param {string} key - 键名
     */
    has(key) {
        const fullKey = this.getKey(key);
        return localStorage.getItem(fullKey) !== null;
    }

    /**
     * 获取所有键名
     */
    keys() {
        const allKeys = Object.keys(localStorage);
        return allKeys
            .filter(key => key.startsWith(this.prefix))
            .map(key => key.substring(this.prefix.length));
    }

    /**
     * 获取存储大小（字节）
     */
    getSize() {
        let size = 0;
        for (const key in localStorage) {
            if (localStorage.hasOwnProperty(key) && key.startsWith(this.prefix)) {
                size += localStorage[key].length + key.length;
            }
        }
        return size;
    }

    /**
     * 批量设置
     * @param {Object} items - 键值对对象
     */
    setMultiple(items) {
        for (const [key, value] of Object.entries(items)) {
            this.set(key, value);
        }
    }

    /**
     * 批量获取
     * @param {Array} keys - 键名数组
     */
    getMultiple(keys) {
        const result = {};
        keys.forEach(key => {
            result[key] = this.get(key);
        });
        return result;
    }

    /**
     * 更新值（基于现有值）
     * @param {string} key - 键名
     * @param {Function} updater - 更新函数
     */
    update(key, updater) {
        const currentValue = this.get(key);
        const newValue = updater(currentValue);
        this.set(key, newValue);
        return newValue;
    }
}

// 创建全局Storage实例
window.storage = new Storage();

// 也可以作为模块导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Storage;
}
