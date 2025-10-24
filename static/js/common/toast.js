/**
 * Toast 通知系统
 * 提供美观的消息提示功能
 */

class ToastManager {
    constructor() {
        this.container = null;
        this.toasts = [];
        this.init();
    }

    init() {
        // 创建Toast容器
        this.container = document.createElement('div');
        this.container.className = 'toast-container';
        document.body.appendChild(this.container);
    }

    /**
     * 显示Toast通知
     * @param {string} message - 消息内容
     * @param {string} type - 类型: success, error, warning, info
     * @param {number} duration - 显示时长(毫秒)，0表示不自动关闭
     */
    show(message, type = 'info', duration = 3000) {
        const toast = this.createToast(message, type);
        this.container.appendChild(toast);
        this.toasts.push(toast);

        // 触发动画
        setTimeout(() => {
            toast.classList.add('fade-in');
        }, 10);

        // 自动关闭
        if (duration > 0) {
            setTimeout(() => {
                this.close(toast);
            }, duration);
        }

        return toast;
    }

    createToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };

        const titles = {
            success: '成功',
            error: '错误',
            warning: '警告',
            info: '提示'
        };

        toast.innerHTML = `
            <div class="toast-icon">${icons[type] || icons.info}</div>
            <div class="toast-content">
                <div class="toast-title">${titles[type] || titles.info}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" aria-label="关闭">×</button>
        `;

        // 关闭按钮事件
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            this.close(toast);
        });

        return toast;
    }

    close(toast) {
        if (!toast || !toast.parentElement) return;

        toast.classList.remove('fade-in');
        toast.classList.add('fade-out');

        setTimeout(() => {
            if (toast.parentElement) {
                this.container.removeChild(toast);
            }
            const index = this.toasts.indexOf(toast);
            if (index > -1) {
                this.toasts.splice(index, 1);
            }
        }, 300);
    }

    // 便捷方法
    success(message, duration = 3000) {
        return this.show(message, 'success', duration);
    }

    error(message, duration = 5000) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration = 4000) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration = 3000) {
        return this.show(message, 'info', duration);
    }

    // 清除所有Toast
    clearAll() {
        this.toasts.forEach(toast => {
            this.close(toast);
        });
    }
}

// 创建全局Toast实例
window.toast = new ToastManager();

// 也可以作为模块导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ToastManager;
}
