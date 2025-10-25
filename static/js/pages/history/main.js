/**
 * 历史页面主入口
 * 负责初始化历史记录管理器并绑定事件
 */

class HistoryPageApp {
    constructor() {
        this.initialized = false;
    }

    /**
     * 初始化应用
     */
    async init() {
        if (this.initialized) return;

        // 初始化历史记录管理器
        const historyList = document.getElementById('historyList');
        if (!historyList) {
            console.error('找不到历史记录容器');
            return;
        }

        this.historyManager = new HistoryManager(historyList);

        // 绑定事件
        this.bindEvents();

        // 加载历史记录
        await this.loadHistory();

        this.initialized = true;
        console.log('历史页面初始化完成');
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 刷新按钮
        const refreshBtn = document.getElementById('refreshHistory');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.handleRefresh());
        }

        // 清空按钮
        const clearBtn = document.getElementById('clearHistory');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.handleClear());
        }
    }

    /**
     * 加载历史记录
     */
    async loadHistory() {
        try {
            await this.historyManager.loadHistory();
        } catch (error) {
            console.error('加载历史记录失败:', error);
        }
    }

    /**
     * 处理刷新
     */
    async handleRefresh() {
        const refreshBtn = document.getElementById('refreshHistory');
        const originalText = refreshBtn.textContent;

        try {
            refreshBtn.disabled = true;
            refreshBtn.textContent = '刷新中...';

            await this.loadHistory();
            toast.success('刷新成功');
        } catch (error) {
            console.error('刷新失败:', error);
        } finally {
            refreshBtn.disabled = false;
            refreshBtn.textContent = originalText;
        }
    }

    /**
     * 处理清空
     */
    async handleClear() {
        await this.historyManager.clearHistory();
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', async () => {
    const app = new HistoryPageApp();
    await app.init();

    // 暴露到全局，方便调试
    window.historyPageApp = app;
});
