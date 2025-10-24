/**
 * 任务管理器
 * 负责文章生成任务的创建、轮询、状态更新
 */

class TaskManager {
    constructor(options = {}) {
        this.stateManager = options.stateManager;
        this.progressArea = options.progressArea;
        this.progressFill = options.progressFill;
        this.progressText = options.progressText;
        this.resultsArea = options.resultsArea;
        this.resultsList = options.resultsList;
        this.generateBtn = options.generateBtn;

        this.statusInterval = null;
        this.POLL_INTERVAL = 2000; // 2秒轮询一次

        this.init();
    }

    init() {
        // 事件委托：处理重试和放弃按钮
        this.resultsList.addEventListener('click', (e) => this.handleResultAction(e));
    }

    /**
     * 开始生成任务
     */
    async startGeneration(topics, topicImageMap) {
        if (topics.length === 0) {
            toast.warning('请至少输入一个文章标题或主题！');
            return;
        }

        // 检查 Pandoc 配置
        try {
            const checkData = await api.checkPandoc();
            if (!checkData.pandoc_configured) {
                toast.error('请先在配置页面设置 Pandoc 可执行文件路径！');
                return;
            }
        } catch (error) {
            toast.error('检查配置时发生错误，请稍后重试');
            return;
        }

        // 重置UI
        this.showProgress();
        this.resultsList.innerHTML = '';
        this.updateProgress(0, '正在启动任务...');
        this.setGenerateButtonState(true, '生成中...');

        try {
            const data = await api.generateArticles(topics, topicImageMap);
            this.stateManager.saveTaskProgress(data.task_id);
            this.startPolling(data.task_id);
            toast.success('任务已启动，开始生成文章...');
        } catch (error) {
            toast.error('启动生成任务失败: ' + error.message);
            this.resetUI();
        }
    }

    /**
     * 开始轮询任务状态
     */
    startPolling(taskId) {
        // 立即执行一次
        this.pollStatus(taskId);

        // 设置定时轮询
        this.statusInterval = setInterval(() => {
            this.pollStatus(taskId);
        }, this.POLL_INTERVAL);
    }

    /**
     * 停止轮询
     */
    stopPolling() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }
    }

    /**
     * 轮询任务状态
     */
    async pollStatus(taskId) {
        try {
            const task = await api.getGenerationStatus(taskId);
            this.updateUI(task);

            if (task.status === 'completed') {
                this.stopPolling();
                this.updateProgress(100, '全部任务已完成！');
                this.setGenerateButtonState(false, '开始生成');
                this.stateManager.clearTaskProgress();
                toast.success('所有文章生成完成！');
            }
        } catch (error) {
            if (error.status === 404) {
                // 任务不存在
                this.stopPolling();
                this.stateManager.clearTaskProgress();
                toast.error('任务状态查询失败，任务可能已丢失');
                this.resetUI();
            } else {
                console.error('轮询状态失败:', error);
            }
        }
    }

    /**
     * 恢复任务进度
     */
    async restoreTaskProgress() {
        const savedTask = this.stateManager.getSavedTask();

        if (!savedTask) return;

        try {
            const task = await api.getGenerationStatus(savedTask.taskId);

            if (task.status === 'running') {
                // 任务仍在运行，恢复轮询
                this.stateManager.currentTaskId = savedTask.taskId;
                this.showProgress();
                this.showResults();
                this.setGenerateButtonState(true, '生成中...');
                this.startPolling(savedTask.taskId);
                this.updateUI(task);
                toast.info('已恢复正在进行的任务');
            } else if (task.status === 'completed') {
                // 任务已完成，显示结果
                this.showProgress();
                this.showResults();
                this.updateUI(task);
                this.updateProgress(100, '全部任务已完成！');
                this.stateManager.clearTaskProgress();
            }
        } catch (error) {
            // 任务不存在，清除保存的数据
            this.stateManager.clearTaskProgress();
            console.error('恢复任务进度失败:', error);
        }
    }

    /**
     * 更新UI
     */
    updateUI(task) {
        console.log('更新UI - 任务状态:', {
            status: task.status,
            total: task.total,
            results: task.results.length,
            errors: task.errors.length,
            progress: task.progress
        });

        // 更新进度
        const completedCount = task.results.length + task.errors.length;
        this.updateProgress(
            task.progress,
            `生成中... (${completedCount}/${task.total}) - ${Math.round(task.progress)}%`
        );

        // 清空并重新渲染结果列表
        this.resultsList.innerHTML = '';

        // 渲染成功结果
        task.results.forEach(result => {
            const item = this.createSuccessItem(result);
            this.resultsList.appendChild(item);
        });

        // 渲染失败结果
        task.errors.forEach(error => {
            const item = this.createErrorItem(error);
            this.resultsList.appendChild(item);
        });

        // 显示结果区域并平滑滚动
        if (task.results.length > 0 || task.errors.length > 0) {
            this.showResults();
            Utils.scrollToElement(this.resultsArea);
        }
    }

    /**
     * 创建成功结果项
     */
    createSuccessItem(result) {
        const item = document.createElement('div');
        item.className = 'result-item success slide-in-left';
        item.innerHTML = `
            <div class="result-title">✓ ${result.article_title}</div>
            <a href="/api/download/${result.filename}" class="download-btn" download>
                📥 下载 Word 文档
            </a>
        `;
        return item;
    }

    /**
     * 创建失败结果项
     */
    createErrorItem(error) {
        const item = document.createElement('div');
        item.className = 'result-item error slide-in-left';
        item.innerHTML = `
            <div class="result-title">✗ ${error.topic}</div>
            <div class="result-info">错误: ${error.error}</div>
            <div class="result-actions">
                <button class="btn btn-secondary btn-small retry-btn" data-topic="${error.topic}">
                    🔄 重试
                </button>
                <button class="btn btn-secondary btn-small discard-btn">
                    ✕ 放弃
                </button>
            </div>
        `;
        return item;
    }

    /**
     * 处理结果项按钮点击
     */
    async handleResultAction(event) {
        const target = event.target;

        // 处理重试按钮
        if (target.classList.contains('retry-btn')) {
            await this.handleRetry(target);
        }

        // 处理放弃按钮
        if (target.classList.contains('discard-btn')) {
            this.handleDiscard(target);
        }
    }

    /**
     * 处理重试
     */
    async handleRetry(button) {
        const topic = button.dataset.topic;
        const taskId = this.stateManager.currentTaskId;

        if (!topic || !taskId) return;

        button.disabled = true;
        button.textContent = '重试中...';

        try {
            await api.retryFailedTopics(taskId, [topic]);

            // 重新启动轮询
            this.setGenerateButtonState(true, '生成中...');
            this.updateProgress(null, '任务已重新提交，正在更新状态...');

            this.stopPolling();
            this.startPolling(taskId);

            toast.info('正在重试生成...');
        } catch (error) {
            toast.error('重试请求失败！');
            button.disabled = false;
            button.textContent = '🔄 重试';
        }
    }

    /**
     * 处理放弃
     */
    handleDiscard(button) {
        const item = button.closest('.result-item');
        item.classList.add('fade-out');
        setTimeout(() => item.remove(), 300);
        toast.info('已放弃该任务');
    }

    /**
     * 更新进度条
     */
    updateProgress(progress, text) {
        if (progress !== null) {
            this.progressFill.style.width = `${progress}%`;
        }
        if (text) {
            this.progressText.textContent = text;
        }
    }

    /**
     * 显示进度区域
     */
    showProgress() {
        this.progressArea.style.display = 'block';
    }

    /**
     * 隐藏进度区域
     */
    hideProgress() {
        this.progressArea.style.display = 'none';
    }

    /**
     * 显示结果区域
     */
    showResults() {
        this.resultsArea.style.display = 'block';
    }

    /**
     * 隐藏结果区域
     */
    hideResults() {
        this.resultsArea.style.display = 'none';
    }

    /**
     * 设置生成按钮状态
     */
    setGenerateButtonState(disabled, text) {
        this.generateBtn.disabled = disabled;
        if (text) {
            this.generateBtn.textContent = text;
        }
    }

    /**
     * 重置UI
     */
    resetUI() {
        this.hideProgress();
        this.setGenerateButtonState(false, '开始生成');
        this.stopPolling();
    }
}

// 导出到全局
window.TaskManager = TaskManager;
