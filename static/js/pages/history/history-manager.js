/**
 * 历史记录管理器
 * 负责加载、显示历史记录
 */

class HistoryManager {
    constructor(container) {
        this.container = container;
    }

    /**
     * 加载历史记录
     */
    async loadHistory() {
        this.showLoading();

        try {
            const data = await api.getHistory();
            this.displayHistory(data.files);
            return data.files;
        } catch (error) {
            console.error('加载历史记录失败:', error);
            this.showError();
            toast.error('加载历史记录失败');
            throw error;
        }
    }

    /**
     * 显示历史记录
     */
    displayHistory(files) {
        if (!files || files.length === 0) {
            this.showEmpty();
            return;
        }

        this.container.innerHTML = '';

        files.forEach((file, index) => {
            const item = this.createHistoryItem(file, index);
            this.container.appendChild(item);
        });

        toast.success(`加载了 ${files.length} 条历史记录`);
    }

    /**
     * 创建历史记录项
     */
    createHistoryItem(file, index) {
        const item = document.createElement('div');
        item.className = 'history-item slide-in-left';
        item.style.animationDelay = `${index * 0.05}s`;

        const sizeFormatted = Utils.formatFileSize(file.size);

        item.innerHTML = `
            <div class="history-item-header">
                <div class="history-item-title">📄 ${file.title}</div>
                <div class="history-item-date">🕒 ${file.created}</div>
            </div>
            <div class="history-item-info">
                <span class="info-label">文件名:</span> ${file.filename}
            </div>
            <div class="history-item-info">
                <span class="info-label">大小:</span> ${sizeFormatted}
            </div>
            <div class="history-item-actions">
                <a href="/api/download/${file.filename}" class="download-btn btn btn-primary btn-small" download>
                    📥 下载
                </a>
                <button class="copy-filename-btn btn btn-secondary btn-small" data-filename="${file.filename}">
                    📋 复制文件名
                </button>
            </div>
        `;

        // 添加复制文件名功能
        const copyBtn = item.querySelector('.copy-filename-btn');
        copyBtn.addEventListener('click', async () => {
            const filename = copyBtn.dataset.filename;
            const success = await Utils.copyToClipboard(filename);
            if (success) {
                toast.success('文件名已复制到剪贴板');
            } else {
                toast.error('复制失败');
            }
        });

        return item;
    }

    /**
     * 显示加载中
     */
    showLoading() {
        this.container.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>加载中...</p>
            </div>
        `;
    }

    /**
     * 显示错误
     */
    showError() {
        this.container.innerHTML = `
            <div class="empty-state">
                <p>❌ 加载失败，请重试</p>
            </div>
        `;
    }

    /**
     * 显示空状态
     */
    showEmpty() {
        this.container.innerHTML = `
            <div class="empty-state">
                <p>📂 暂无历史记录</p>
                <p class="help-text">生成文章后会在这里显示</p>
            </div>
        `;
    }

    /**
     * 清空历史记录
     */
    async clearHistory() {
        const confirmed = confirm('确定要清空所有历史记录吗？此操作无法撤销！');

        if (!confirmed) {
            return false;
        }

        toast.warning('清空历史功能需要手动删除 output 目录下的文件');

        // TODO: 可以添加后端API来实现清空功能
        return false;
    }
}

// 导出到全局
window.HistoryManager = HistoryManager;
