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
        this.batchActions = document.getElementById('batchActions');
        this.retryAllBtn = document.getElementById('retryAllBtn');
        this.discardAllBtn = document.getElementById('discardAllBtn');

        this.statusInterval = null;
        this.POLL_INTERVAL = 2000;
        this.hasScrolledToResults = false;
        this.discardedTopics = new Set();
        this.retryingTopics = new Set();

        this.init();
    }

    init() {
        this.resultsList.addEventListener('click', (e) => this.handleResultAction(e));
        if (this.retryAllBtn) this.retryAllBtn.addEventListener('click', () => this.handleRetryAll());
        if (this.discardAllBtn) this.discardAllBtn.addEventListener('click', () => this.handleDiscardAll());
    }

    async startGeneration(topics, topicImageMap) {
        if (topics.length === 0) {
            toast.warning('请至少输入一个文章标题或主题！');
            return;
        }
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

        this.resetUIState();
        this.renderInitialPending(topics);

        try {
            const data = await api.generateArticles(topics, topicImageMap);
            this.stateManager.saveTaskProgress(data.task_id, topics);
            this.startPolling(data.task_id);
            toast.success('任务已启动，开始生成文章...');
        } catch (error) {
            toast.error('启动生成任务失败: ' + error.message);
            this.resetUI();
        }
    }

    startPolling(taskId) {
        this.stopPolling();
        this.pollStatus(taskId); // 立即执行一次
        this.statusInterval = setInterval(() => this.pollStatus(taskId), this.POLL_INTERVAL);
    }

    stopPolling() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }
    }

    async pollStatus(taskId) {
        try {
            const task = await api.getGenerationStatus(taskId);
            this.updateUI(task);

            if (task.status === 'completed') {
                this.stopPolling();
                this.finalizeTaskUI(task); // 使用新的最终处理函数
            }
        } catch (error) {
            if (error.status === 404) {
                this.stopPolling();
                this.stateManager.clearTaskProgress();
                this.resetUI();
                toast.error('任务已失效或在服务器上被清除，请重新开始');
            } else {
                console.error('轮询状态失败:', error);
            }
        }
    }

    async restoreTaskProgress() {
        const savedTask = this.stateManager.getSavedTask();
        if (!savedTask || !savedTask.taskId) return;

        try {
            // 首先渲染出所有的待处理项
            const initialTopics = savedTask.topics || [];
            this.resetUIState();
            this.renderInitialPending(initialTopics);

            const task = await api.getGenerationStatus(savedTask.taskId);

            this.stateManager.currentTaskId = savedTask.taskId;
            this.updateUI(task); // 使用当前状态更新UI

            if (task.status === 'running') {
                this.startPolling(savedTask.taskId);
                toast.info('已恢复正在进行的任务');
            } else if (task.status === 'completed') {
                this.finalizeTaskUI(task); // 如果任务已完成，执行最终处理
            }
        } catch (error) {
            this.stateManager.clearTaskProgress();
            console.error('恢复任务进度失败:', error);
            this.resetUI();
        }
    }


    updateUI(task) {
        const newOutcomes = new Set([...task.results.map(r => r.topic), ...task.errors.map(e => e.topic)]);
        this.retryingTopics.forEach(topic => {
            if (newOutcomes.has(topic)) {
                this.retryingTopics.delete(topic);
            }
        });

        const filteredErrors = task.errors.filter(e => !this.discardedTopics.has(e.topic));
        const completedCount = task.results.length + filteredErrors.length;
        const totalCount = task.total - this.discardedTopics.size;
        const progress = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

        this.updateProgress(progress, `生成中... (${completedCount}/${totalCount})`);

        task.results.forEach(result => this.replacePlaceholder(result.topic, this.createSuccessItem(result)));
        filteredErrors.forEach(error => this.replacePlaceholder(error.topic, this.createErrorItem(error, this.retryingTopics.has(error.topic))));

        const canRetryCount = filteredErrors.filter(e => !this.retryingTopics.has(e.topic)).length;
        if(this.batchActions) this.batchActions.style.display = canRetryCount > 1 ? 'flex' : 'none';

        if ((task.results.length > 0 || filteredErrors.length > 0) && !this.hasScrolledToResults) {
            this.showResults();
            Utils.scrollToElement(this.resultsArea);
            this.hasScrolledToResults = true;
        }
    }

    finalizeTaskUI(task) {
        // --- 前端安全网机制 ---
        const processedTopics = new Set([...task.results.map(r => r.topic), ...task.errors.map(e => e.topic)]);
        const pendingItems = this.resultsList.querySelectorAll('.result-item.pending');

        pendingItems.forEach(item => {
            const topic = item.dataset.topic;
            if (!processedTopics.has(topic)) {
                console.warn(`检测到幽灵任务 (UI): ${topic}，强制标记为失败`);
                const ghostError = { topic: topic, error: '任务状态未知，请重试', retry_count: 0 };
                this.replacePlaceholder(topic, this.createErrorItem(ghostError, false));
            }
        });

        const finalErrors = Array.from(this.resultsList.querySelectorAll('.result-item.error')).length;

        if (finalErrors === 0) {
            this.updateProgress(100, '全部任务已完成！');
            this.setGenerateButtonState(false, '开始生成');
            this.stateManager.clearTaskProgress();
            toast.success('所有文章生成完成！');
        } else {
            this.updateProgress(100, `任务完成，但有 ${finalErrors} 个失败项`);
            toast.warning(`任务完成，但有 ${finalErrors} 个项目失败，您可以选择重试`);
            // 保持生成按钮禁用，让用户通过重试/放弃来继续
            this.setGenerateButtonState(true, '任务已完成');
        }

        const canRetryCount = this.resultsList.querySelectorAll('.retry-btn').length;
        if(this.batchActions) this.batchActions.style.display = canRetryCount > 1 ? 'flex' : 'none';
    }


    replacePlaceholder(topic, newItem) {
        const placeholder = this.resultsList.querySelector(`.result-item[data-topic="${topic}"]`);
        if (placeholder) {
            placeholder.replaceWith(newItem);
        } else {
            // 如果没有找到占位符（例如在恢复任务时），则直接添加
            this.resultsList.appendChild(newItem);
        }
    }

    createSuccessItem(result) {
        const item = document.createElement('div');
        item.className = 'result-item success slide-in-left';
        item.dataset.topic = result.topic;
        item.innerHTML = `
            <div class="result-title">✓ ${result.article_title}</div>
            <a href="/api/download/${result.filename}" class="download-btn" download>📥 下载 Word 文档</a>
        `;
        return item;
    }

    createErrorItem(error, isRetrying) {
        const item = document.createElement('div');
        item.className = 'result-item error slide-in-left';
        item.dataset.topic = error.topic;
        const retryHint = error.retry_count > 0 ? ` (已重试 ${error.retry_count} 次)` : '';
        const title = error.topic.length > 50 ? error.topic.substring(0, 50) + '...' : error.topic;

        if (isRetrying) {
            item.innerHTML = `<div class="result-title">⏳ ${title}${retryHint}</div><div class="result-info" style="color: #007bff;">正在重试...</div>`;
        } else {
            item.innerHTML = `
                <div class="result-title">✗ ${title}${retryHint}</div>
                <div class="result-info">错误: ${error.error}</div>
                <div class="result-actions">
                    <button class="btn btn-secondary btn-small retry-btn" data-topic="${error.topic}">🔄 重试</button>
                    <button class="btn btn-secondary btn-small discard-btn" data-topic="${error.topic}">✕ 放弃</button>
                </div>`;
        }
        return item;
    }

    createPendingItem(topic) {
        const item = document.createElement('div');
        item.className = 'result-item pending';
        item.dataset.topic = topic;
        const title = topic.length > 50 ? topic.substring(0, 50) + '...' : topic;
        item.innerHTML = `<div class="result-title">⏳ ${title}</div><div class="result-info">正在等待生成...</div>`;
        return item;
    }

    async handleResultAction(event) {
        const target = event.target;
        if (target.classList.contains('retry-btn')) await this.handleRetry(target);
        if (target.classList.contains('discard-btn')) this.handleDiscard(target);
    }

    async handleRetry(button) {
        const topic = button.dataset.topic;
        let taskId = this.stateManager.currentTaskId || '';
        if (!topic) return;

        this.retryingTopics.add(topic);
        const item = button.closest('.result-item');
        const retryCount = (item.innerHTML.match(/已重试 (\d+)/)?.[1] || 0);
        const errorData = { topic, error: '', retry_count: parseInt(retryCount) };
        this.replacePlaceholder(topic, this.createErrorItem(errorData, true));

        try {
            const response = await api.retryFailedTopics(taskId, [topic]);
            if (response.new_task && response.task_id) {
                this.stateManager.saveTaskProgress(response.task_id, this.stateManager.getSavedTask().topics);
                this.startPolling(response.task_id);
                toast.info('原任务已失效，已创建新任务重试');
            } else {
                this.startPolling(taskId); // 继续轮询同一个任务
            }
            toast.success('重试请求已提交！');
        } catch (error) {
            this.retryingTopics.delete(topic);
            toast.error('重试请求失败: ' + error.message);
            errorData.error = error.message;
            this.replacePlaceholder(topic, this.createErrorItem(errorData, false));
        }
    }

    handleDiscard(button) {
        const topic = button.dataset.topic;
        if (!topic) return;
        this.discardedTopics.add(topic);
        const item = button.closest('.result-item');
        item.classList.add('fade-out');
        setTimeout(() => item.remove(), 300);
        toast.success(`已放弃任务: ${topic.substring(0, 30)}...`);
    }

    async handleRetryAll() {
        // ... (内容未改变，为简洁省略) ...
        let taskId = this.stateManager.currentTaskId || '';
        const failedTopics = Array.from(this.resultsList.querySelectorAll('.retry-btn'))
                                 .map(btn => btn.dataset.topic)
                                 .filter(topic => topic && !this.retryingTopics.has(topic));

        if (failedTopics.length === 0) {
            toast.warning('没有可重试的失败项');
            return;
        }
        if (!confirm(`确定要重试全部 ${failedTopics.length} 个失败项吗？`)) return;

        failedTopics.forEach(topic => {
            this.retryingTopics.add(topic);
            const item = this.resultsList.querySelector(`.result-item[data-topic="${topic}"]`);
            if(item) {
                const retryCount = (item.innerHTML.match(/已重试 (\d+)/)?.[1] || 0);
                this.replacePlaceholder(topic, this.createErrorItem({ topic, error: '', retry_count: parseInt(retryCount) }, true));
            }
        });

        this.retryAllBtn.disabled = true;
        this.retryAllBtn.textContent = '重试中...';

        try {
            const response = await api.retryFailedTopics(taskId, failedTopics);
            if (response.new_task && response.task_id) {
                this.stateManager.saveTaskProgress(response.task_id, this.stateManager.getSavedTask().topics);
                this.startPolling(response.task_id);
                toast.info('原任务已失效，已创建新任务进行批量重试');
            } else {
                this.startPolling(taskId);
            }
            toast.success(`已提交 ${failedTopics.length} 个主题重试！`);
        } catch (error) {
            failedTopics.forEach(topic => this.retryingTopics.delete(topic));
            toast.error('批量重试请求失败: ' + error.message);
        } finally {
            this.retryAllBtn.disabled = false;
            this.retryAllBtn.textContent = '🔄 重试全部失败项';
        }
    }

    handleDiscardAll() {
        // ... (内容未改变，为简洁省略) ...
        const failedItems = this.resultsList.querySelectorAll('.result-item.error .discard-btn');
        if (failedItems.length === 0) {
            toast.warning('没有可放弃的失败项');
            return;
        }
        if (!confirm(`确定要放弃全部 ${failedItems.length} 个失败项吗？`)) return;

        failedItems.forEach(btn => this.handleDiscard(btn));
    }

    resetUIState() {
        this.stopPolling();
        this.setGenerateButtonState(true, '生成中...');
        this.updateProgress(0, '正在启动任务...');
        this.showProgress();
        this.resultsList.innerHTML = '';
        this.hasScrolledToResults = false;
        this.discardedTopics.clear();
        this.retryingTopics.clear();
    }

    renderInitialPending(topics) {
        this.resultsList.innerHTML = '';
        topics.forEach(topic => this.resultsList.appendChild(this.createPendingItem(topic)));
        if (topics.length > 0) this.showResults();
    }

    resetUI() {
        this.hideProgress();
        this.hideResults();
        this.setGenerateButtonState(false, '开始生成');
        this.stopPolling();
    }

    updateProgress(progress, text) {
        this.progressFill.style.width = `${Math.max(0, Math.min(100, progress))}%`;
        this.progressText.textContent = text;
    }

    showProgress() { this.progressArea.style.display = 'block'; }
    hideProgress() { this.progressArea.style.display = 'none'; }
    showResults() { this.resultsArea.style.display = 'block'; }
    hideResults() { this.resultsArea.style.display = 'none'; }
    setGenerateButtonState(disabled, text) {
        this.generateBtn.disabled = disabled;
        if (text) this.generateBtn.textContent = text;
    }
}

window.TaskManager = TaskManager;
