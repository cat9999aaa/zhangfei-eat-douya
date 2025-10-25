/**
 * Tab 标签页管理器
 * 负责配置页面的Tab切换
 */

class TabManager {
    constructor(container) {
        this.container = container;
        this.currentTab = null;
        this.tabs = new Map();
        this.init();
    }

    /**
     * 初始化Tab系统
     */
    init() {
        // 查找所有Tab按钮
        const tabButtons = this.container.querySelectorAll('.tab-button');
        const tabPanes = this.container.querySelectorAll('.tab-pane');

        // 注册Tab
        tabButtons.forEach((button, index) => {
            const tabId = button.dataset.tab;
            const pane = this.container.querySelector(`#${tabId}`);

            if (pane) {
                this.tabs.set(tabId, {
                    button,
                    pane,
                    index
                });

                // 绑定点击事件
                button.addEventListener('click', () => this.switchTab(tabId));
            }
        });

        // 激活第一个Tab或URL指定的Tab
        const urlParams = new URLSearchParams(window.location.search);
        const initialTab = urlParams.get('tab') || this.getFirstTabId();

        if (initialTab) {
            this.switchTab(initialTab);
        }

        // 保存当前Tab到LocalStorage
        this.restoreLastTab();
    }

    /**
     * 切换Tab
     */
    switchTab(tabId) {
        const tab = this.tabs.get(tabId);

        if (!tab) {
            console.warn(`Tab ${tabId} not found`);
            return;
        }

        // 如果已经是当前Tab，不做操作
        if (this.currentTab === tabId) {
            return;
        }

        // 隐藏所有Tab
        this.tabs.forEach((t, id) => {
            t.button.classList.remove('active');
            t.pane.classList.remove('active');
        });

        // 显示目标Tab
        tab.button.classList.add('active');
        tab.pane.classList.add('active');

        // 更新当前Tab
        this.currentTab = tabId;

        // 保存到LocalStorage
        storage.set('config_current_tab', tabId);

        // 更新URL（不刷新页面）
        this.updateURL(tabId);

        // 滚动到顶部
        window.scrollTo({ top: 0, behavior: 'smooth' });

        // 触发自定义事件
        this.container.dispatchEvent(new CustomEvent('tabChanged', {
            detail: { tabId, tab }
        }));
    }

    /**
     * 获取第一个Tab的ID
     */
    getFirstTabId() {
        return Array.from(this.tabs.keys())[0];
    }

    /**
     * 恢复上次的Tab
     */
    restoreLastTab() {
        const lastTab = storage.get('config_current_tab');

        if (lastTab && this.tabs.has(lastTab)) {
            this.switchTab(lastTab);
        }
    }

    /**
     * 更新URL参数
     */
    updateURL(tabId) {
        const url = new URL(window.location);
        url.searchParams.set('tab', tabId);
        window.history.replaceState({}, '', url);
    }

    /**
     * 获取当前Tab ID
     */
    getCurrentTab() {
        return this.currentTab;
    }

    /**
     * 切换到下一个Tab
     */
    nextTab() {
        const currentIndex = this.tabs.get(this.currentTab)?.index || 0;
        const tabIds = Array.from(this.tabs.keys());
        const nextIndex = (currentIndex + 1) % tabIds.length;
        this.switchTab(tabIds[nextIndex]);
    }

    /**
     * 切换到上一个Tab
     */
    prevTab() {
        const currentIndex = this.tabs.get(this.currentTab)?.index || 0;
        const tabIds = Array.from(this.tabs.keys());
        const prevIndex = (currentIndex - 1 + tabIds.length) % tabIds.length;
        this.switchTab(tabIds[prevIndex]);
    }
}

// 导出到全局
window.TabManager = TabManager;
