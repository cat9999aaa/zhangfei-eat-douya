/**
 * 写作页面主入口
 * 负责初始化所有模块并协调它们的交互
 */

class WritePageApp {
    constructor() {
        // DOM元素
        this.elements = {
            topicsContainer: document.getElementById('topicsContainer'),
            addTopicBtn: document.getElementById('addTopicBtn'),
            enableImage: document.getElementById('enableImage'),
            generateBtn: document.getElementById('generateBtn'),
            clearBtn: document.getElementById('clearBtn'),
            progressArea: document.getElementById('progressArea'),
            progressFill: document.getElementById('progressFill'),
            progressText: document.getElementById('progressText'),
            resultsArea: document.getElementById('resultsArea'),
            resultsList: document.getElementById('resultsList')
        };

        this.initialized = false;
    }

    /**
     * 初始化应用
     */
    async init() {
        if (this.initialized) return;

        // 初始化状态管理器
        this.stateManager = window.writeStateManager;

        // 初始化主题管理器
        this.topicManager = new TopicManager({
            container: this.elements.topicsContainer,
            addButton: this.elements.addTopicBtn,
            clearButton: this.elements.clearBtn,
            maxTopics: 50,
            stateManager: this.stateManager,
            onImageSettingClick: (index) => this.imageModal.open(index)
        });

        // 初始化任务管理器
        this.taskManager = new TaskManager({
            stateManager: this.stateManager,
            progressArea: this.elements.progressArea,
            progressFill: this.elements.progressFill,
            progressText: this.elements.progressText,
            resultsArea: this.elements.resultsArea,
            resultsList: this.elements.resultsList,
            generateBtn: this.elements.generateBtn
        });

        // 初始化图片模态框
        this.imageModal = new ImageModal({
            stateManager: this.stateManager,
            topicManager: this.topicManager
        });

        // 恢复页面状态
        this.topicManager.restoreState();

        // 恢复任务进度
        await this.taskManager.restoreTaskProgress();

        // 检查 Pandoc 配置
        await this.checkPandocConfig();

        // 绑定生成按钮事件
        this.bindEvents();

        this.initialized = true;
        console.log('写作页面初始化完成');
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 生成按钮
        this.elements.generateBtn.addEventListener('click', () => this.handleGenerate());

        // 图片选项变化时保存状态
        this.elements.enableImage.addEventListener('change', () => {
            this.topicManager.saveState();
        });
    }

    /**
     * 检查 Pandoc 配置
     */
    async checkPandocConfig() {
        try {
            const checkData = await api.checkPandoc();

            if (!checkData.pandoc_configured) {
                this.showPandocWarning();
            }
        } catch (error) {
            console.error('检查 Pandoc 配置失败:', error);
        }
    }

    /**
     * 显示 Pandoc 警告
     */
    showPandocWarning() {
        const warningDiv = document.createElement('div');
        warningDiv.className = 'alert alert-warning fade-in';
        warningDiv.style.cssText = `
            background: linear-gradient(135deg, #fff3cd 0%, #ffe8a1 100%);
            border: 2px solid var(--warning-color);
            color: #856404;
            padding: 15px 20px;
            margin-bottom: 20px;
            border-radius: var(--border-radius);
            text-align: center;
            font-weight: 600;
            box-shadow: var(--shadow-small);
        `;
        warningDiv.innerHTML = `
            ⚠️ 请先在<a href="/config" style="color: #007bff; text-decoration: underline; font-weight: bold;">配置页面</a>设置 Pandoc 路径，否则无法生成文章！
        `;

        const mainContent = document.querySelector('.main-content') || document.querySelector('.page-container');
        if (mainContent && mainContent.firstChild) {
            mainContent.insertBefore(warningDiv, mainContent.firstChild);
        }
    }

    /**
     * 处理生成按钮点击
     */
    async handleGenerate() {
        const topics = this.topicManager.getAllTopics();
        const topicImageMap = this.stateManager.buildTopicImageMap(topics);

        await this.taskManager.startGeneration(topics, topicImageMap);
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', async () => {
    const app = new WritePageApp();
    await app.init();

    // 暴露到全局，方便调试
    window.writePageApp = app;
});
