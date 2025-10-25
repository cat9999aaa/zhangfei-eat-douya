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
        this.POLL_INTERVAL = 2000; // 2秒轮询一次

        // 跟踪是否已经滚动过（修复自动滚动问题）
        this.hasScrolledToResults = false;

        // 跟踪已放弃和正在重试的主题
        this.discardedTopics = new Set();
        this.retryingTopics = new Set();

        // 跟踪重试次数
        this.retryCount = new Map(); // topic -> count

        // 跟踪上次的结果数量（用于减少日志输出）
        this.lastResultCount = 0;
        this.lastErrorCount = 0;

        // 建立topic到原始主题的映射（用于清除重试状态）
        this.topicMap = new Map(); // topic from API -> original input topic

        this.init();
    }

    init() {
        // 事件委托：处理重试和放弃按钮
        this.resultsList.addEventListener('click', (e) => this.handleResultAction(e));

        // 批量操作按钮
        this.retryAllBtn.addEventListener('click', () => this.handleRetryAll());
        this.discardAllBtn.addEventListener('click', () => this.handleDiscardAll());
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

        // 重置UI和状态
        this.showProgress();
        this.resultsList.innerHTML = '';
        this.updateProgress(0, '正在启动任务...');
        this.setGenerateButtonState(true, '生成中...');

        // 重置跟踪状态
        this.hasScrolledToResults = false;
        this.discardedTopics.clear();
        this.retryingTopics.clear();
        this.retryCount.clear();
        this.lastResultCount = 0;
        this.lastErrorCount = 0;
        this.topicMap.clear();

        // 建立初始topic映射
        topics.forEach(topic => {
            this.topicMap.set(topic, topic);
        });

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
        // 过滤掉已放弃的主题
        const filteredErrors = task.errors.filter(error =>
            !this.discardedTopics.has(error.topic)
        );

        // 计算实际完成数（排除正在重试的）
        // 正在重试的主题不应该计入已完成
        const retryingErrorCount = filteredErrors.filter(error =>
            this.retryingTopics.has(error.topic)
        ).length;

        const actualCompletedCount = task.results.length + filteredErrors.length - retryingErrorCount;
        const discardedCount = this.discardedTopics.size;
        const displayTotal = task.total - discardedCount;

        // 前端重新计算进度（避免后端进度不一致）
        const actualProgress = displayTotal > 0 ? (actualCompletedCount / displayTotal) * 100 : 0;

        // 只在结果数量有变化时输出日志（减少日志刷屏）
        if (task.results.length !== this.lastResultCount || filteredErrors.length !== this.lastErrorCount) {
            console.log('更新UI - 任务状态:', {
                status: task.status,
                total: task.total,
                displayTotal: displayTotal,
                results: task.results.length,
                errors: filteredErrors.length,
                retrying: retryingErrorCount,
                actualCompleted: actualCompletedCount,
                progress: Math.round(actualProgress) + '%'
            });
            this.lastResultCount = task.results.length;
            this.lastErrorCount = filteredErrors.length;
        }

        this.updateProgress(
            actualProgress,
            `生成中... (${actualCompletedCount}/${displayTotal}) - ${Math.round(actualProgress)}%`
        );

        // 清空并重新渲染结果列表
        this.resultsList.innerHTML = '';

        // 渲染成功结果
        task.results.forEach(result => {
            const item = this.createSuccessItem(result);
            this.resultsList.appendChild(item);

            // 清除成功结果的重试状态
            // 检查所有正在重试的主题，看是否有匹配的
            for (const retryingTopic of this.retryingTopics) {
                // 如果result中的topic字段存在且匹配，或者通过映射匹配
                if (result.topic === retryingTopic ||
                    this.topicMap.get(result.topic) === retryingTopic) {
                    this.retryingTopics.delete(retryingTopic);
                    break;
                }
            }
        });

        // 渲染失败结果
        const failedNotRetrying = []; // 收集失败且未在重试中的主题
        filteredErrors.forEach(error => {
            const isRetrying = this.retryingTopics.has(error.topic);
            const retryTimes = this.retryCount.get(error.topic) || 0;
            const item = this.createErrorItem(error, isRetrying, retryTimes);
            this.resultsList.appendChild(item);

            if (!isRetrying) {
                failedNotRetrying.push(error.topic);
            }
        });

        // 根据失败项数量显示/隐藏批量操作按钮
        if (failedNotRetrying.length > 1) {
            this.batchActions.style.display = 'flex';
        } else {
            this.batchActions.style.display = 'none';
        }

        // 显示结果区域，只在第一次时滚动
        if (task.results.length > 0 || filteredErrors.length > 0) {
            this.showResults();

            // 只在第一次显示结果时滚动（修复自动滚动问题）
            if (!this.hasScrolledToResults) {
                Utils.scrollToElement(this.resultsArea);
                this.hasScrolledToResults = true;
            }
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
    createErrorItem(error, isRetrying = false, retryTimes = 0) {
        const item = document.createElement('div');
        item.className = 'result-item error slide-in-left';

        if (isRetrying) {
            // 正在重试的状态
            const retryText = retryTimes > 1 ? `第 ${retryTimes} 次重试中...` : '正在重试生成...';
            item.innerHTML = `
                <div class="result-title">⏳ ${error.topic}</div>
                <div class="result-info" style="color: #007bff;">${retryText}</div>
                <div class="result-actions">
                    <button class="btn btn-secondary btn-small" disabled>
                        🔄 重试中...
                    </button>
                </div>
            `;
        } else {
            // 失败状态
            const retryHint = retryTimes > 0 ? ` (已重试 ${retryTimes} 次)` : '';
            item.innerHTML = `
                <div class="result-title">✗ ${error.topic}${retryHint}</div>
                <div class="result-info">错误: ${error.error}</div>
                <div class="result-actions">
                    <button class="btn btn-secondary btn-small retry-btn" data-topic="${error.topic}">
                        🔄 重试
                    </button>
                    <button class="btn btn-secondary btn-small discard-btn" data-topic="${error.topic}">
                        ✕ 放弃
                    </button>
                </div>
            `;
        }

        return item;
    }

    /**
     * 处理结果项按钮点击
     */
    async handleResultAction(event) {
        const target = event.target;
        console.log('按钮点击事件触发', target.className, target.textContent);

        // 处理重试按钮
        if (target.classList.contains('retry-btn')) {
            console.log('检测到重试按钮点击');
            await this.handleRetry(target);
        }

        // 处理放弃按钮
        if (target.classList.contains('discard-btn')) {
            console.log('检测到放弃按钮点击');
            this.handleDiscard(target);
        }
    }

    /**
     * 处理重试
     */
    async handleRetry(button) {
        const topic = button.dataset.topic;
        const taskId = this.stateManager.currentTaskId;

        console.log('handleRetry 被调用', { topic, taskId });

        if (!topic || !taskId) {
            console.error('缺少必要参数', { topic, taskId });
            toast.error('重试失败：缺少必要信息');
            return;
        }

        // 增加重试次数
        const currentCount = this.retryCount.get(topic) || 0;
        this.retryCount.set(topic, currentCount + 1);
        console.log('重试次数:', currentCount + 1);

        // 立即添加到重试集合，提供即时反馈
        this.retryingTopics.add(topic);

        // 立即更新UI显示重试状态
        const item = button.closest('.result-item');
        const retryText = currentCount > 0 ? `第 ${currentCount + 1} 次重试中...` : '正在重试生成...';
        item.querySelector('.result-title').innerHTML = `⏳ ${topic}`;
        item.querySelector('.result-info').innerHTML = `<span style="color: #007bff;">正在提交重试请求...</span>`;
        button.disabled = true;
        button.textContent = '🔄 重试中...';

        console.log('UI已更新为重试中状态');

        try {
            console.log('调用 API 重试:', taskId, [topic]);
            const response = await api.retryFailedTopics(taskId, [topic]);
            console.log('API 响应:', response);

            // 更新状态提示
            item.querySelector('.result-info').innerHTML = `<span style="color: #007bff;">${retryText}</span>`;

            // 重新启动轮询
            this.setGenerateButtonState(true, '生成中...');

            this.stopPolling();
            this.startPolling(taskId);

            toast.success('重试请求已提交！');
            console.log('重试请求提交成功');
        } catch (error) {
            console.error('重试请求失败:', error);

            // 重试失败，从重试集合中移除，并减少计数
            this.retryingTopics.delete(topic);
            this.retryCount.set(topic, currentCount);

            toast.error('重试请求失败: ' + error.message);

            // 恢复错误显示
            const retryHint = currentCount > 0 ? ` (已重试 ${currentCount} 次)` : '';
            item.querySelector('.result-title').innerHTML = `✗ ${topic}${retryHint}`;
            item.querySelector('.result-info').innerHTML = `错误: ${error.message}`;
            button.disabled = false;
            button.textContent = '🔄 重试';
        }
    }

    /**
     * 处理放弃
     */
    handleDiscard(button) {
        const topic = button.dataset.topic;

        console.log('handleDiscard 被调用', { topic });

        if (!topic) {
            console.error('放弃操作缺少topic参数');
            return;
        }

        // 立即禁用所有按钮并更新文本，提供即时反馈
        const item = button.closest('.result-item');
        const retryBtn = item.querySelector('.retry-btn');
        const discardBtn = item.querySelector('.discard-btn');

        if (retryBtn) retryBtn.disabled = true;
        if (discardBtn) {
            discardBtn.disabled = true;
            discardBtn.textContent = '✕ 放弃中...';
        }

        console.log('放弃按钮UI已更新');

        // 添加到放弃集合
        this.discardedTopics.add(topic);

        // 如果在重试集合中，也移除
        if (this.retryingTopics.has(topic)) {
            this.retryingTopics.delete(topic);
        }

        // 显示即时反馈
        toast.info('正在放弃该任务...');

        // 添加淡出动画并移除
        item.classList.add('fade-out');
        setTimeout(() => {
            item.remove();
            toast.success('已成功放弃该任务');
            console.log('任务已从列表中移除');
        }, 300);
    }

    /**
     * 批量重试所有失败项
     */
    async handleRetryAll() {
        const taskId = this.stateManager.currentTaskId;
        if (!taskId) return;

        // 收集所有失败且未在重试中的主题
        const failedTopics = [];
        const retryButtons = this.resultsList.querySelectorAll('.retry-btn:not(:disabled)');

        retryButtons.forEach(button => {
            const topic = button.dataset.topic;
            if (topic && !this.retryingTopics.has(topic)) {
                failedTopics.push(topic);
            }
        });

        if (failedTopics.length === 0) {
            toast.warning('没有可重试的失败项');
            return;
        }

        // 确认操作
        if (!confirm(`确定要重试全部 ${failedTopics.length} 个失败项吗？`)) {
            return;
        }

        // 标记所有主题为重试中
        failedTopics.forEach(topic => {
            const currentCount = this.retryCount.get(topic) || 0;
            this.retryCount.set(topic, currentCount + 1);
            this.retryingTopics.add(topic);
        });

        // 禁用批量按钮
        this.retryAllBtn.disabled = true;
        this.retryAllBtn.textContent = '重试中...';

        try {
            await api.retryFailedTopics(taskId, failedTopics);

            // 重新启动轮询
            this.setGenerateButtonState(true, '生成中...');
            this.stopPolling();
            this.startPolling(taskId);

            toast.success(`已提交 ${failedTopics.length} 个主题重试！`);
        } catch (error) {
            // 重试失败，恢复状态
            failedTopics.forEach(topic => {
                this.retryingTopics.delete(topic);
                const currentCount = this.retryCount.get(topic) || 0;
                this.retryCount.set(topic, Math.max(0, currentCount - 1));
            });

            toast.error('批量重试请求失败: ' + error.message);
        } finally {
            this.retryAllBtn.disabled = false;
            this.retryAllBtn.textContent = '🔄 重试全部失败项';
        }
    }

    /**
     * 批量放弃所有失败项
     */
    async handleDiscardAll() {
        // 收集所有失败项
        const failedItems = this.resultsList.querySelectorAll('.result-item.error');

        if (failedItems.length === 0) {
            toast.warning('没有可放弃的失败项');
            return;
        }

        // 确认操作
        if (!confirm(`确定要放弃全部 ${failedItems.length} 个失败项吗？`)) {
            return;
        }

        // 立即禁用批量按钮并更新文本，提供即时反馈
        this.discardAllBtn.disabled = true;
        this.discardAllBtn.textContent = '✕ 放弃中...';

        // 显示即时反馈
        toast.info(`正在放弃 ${failedItems.length} 个失败项...`);

        // 收集所有主题并添加到放弃集合
        failedItems.forEach(item => {
            const discardBtn = item.querySelector('.discard-btn');
            const retryBtn = item.querySelector('.retry-btn');

            // 禁用所有按钮
            if (discardBtn) {
                discardBtn.disabled = true;
                const topic = discardBtn.dataset.topic;
                if (topic) {
                    this.discardedTopics.add(topic);

                    // 如果在重试集合中，也移除
                    if (this.retryingTopics.has(topic)) {
                        this.retryingTopics.delete(topic);
                    }
                }
            }
            if (retryBtn) retryBtn.disabled = true;

            // 添加淡出动画
            item.classList.add('fade-out');
        });

        // 等待动画完成后移除并恢复按钮状态
        setTimeout(() => {
            failedItems.forEach(item => item.remove());

            // 恢复按钮状态
            this.discardAllBtn.disabled = false;
            this.discardAllBtn.textContent = '✕ 放弃全部失败项';

            // 隐藏批量操作按钮（因为没有失败项了）
            this.batchActions.style.display = 'none';

            // 显示成功提示
            toast.success(`已成功放弃 ${failedItems.length} 个失败项`);
        }, 300);
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
