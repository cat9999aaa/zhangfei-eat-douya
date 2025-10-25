/**
 * API 测试器
 * 负责测试各种 API 连接
 */

class APITester {
    constructor() {
        this.initializeListeners();
    }

    /**
     * 初始化测试按钮监听器
     */
    initializeListeners() {
        // Unsplash测试
        const testUnsplashBtn = document.getElementById('testUnsplash');
        if (testUnsplashBtn) {
            testUnsplashBtn.addEventListener('click', () => this.testUnsplash());
        }

        // Pexels测试
        const testPexelsBtn = document.getElementById('testPexels');
        if (testPexelsBtn) {
            testPexelsBtn.addEventListener('click', () => this.testPexels());
        }

        // Pixabay测试
        const testPixabayBtn = document.getElementById('testPixabay');
        if (testPixabayBtn) {
            testPixabayBtn.addEventListener('click', () => this.testPixabay());
        }

        // 主模型测试
        const testDefaultModelBtn = document.getElementById('testDefaultModel');
        if (testDefaultModelBtn) {
            testDefaultModelBtn.addEventListener('click', () => this.testDefaultModel());
        }

        // 摘要模型测试
        const testSummaryModelBtn = document.getElementById('testSummaryModel');
        if (testSummaryModelBtn) {
            testSummaryModelBtn.addEventListener('click', () => this.testSummaryModel());
        }

        // ComfyUI测试
        const testComfyuiBtn = document.getElementById('testComfyui');
        if (testComfyuiBtn) {
            testComfyuiBtn.addEventListener('click', () => this.testComfyUI());
        }

        // Gemini 图像生成测试
        const testGeminiImageBtn = document.getElementById('testGeminiImage');
        if (testGeminiImageBtn) {
            testGeminiImageBtn.addEventListener('click', () => this.testGeminiImage());
        }

        // 加载 Gemini 图像模型列表
        const loadGeminiImageModelsBtn = document.getElementById('loadGeminiImageModels');
        if (loadGeminiImageModelsBtn) {
            loadGeminiImageModelsBtn.addEventListener('click', () => this.loadGeminiImageModels());
        }
    }

    /**
     * 测试 Unsplash API
     */
    async testUnsplash() {
        const apiKeyInput = document.getElementById('unsplashKey');
        const apiKey = apiKeyInput.value.trim();
        const resultEl = document.getElementById('unsplashTestResult');
        const btn = document.getElementById('testUnsplash');

        // 检查是否有已保存的配置（通过placeholder判断）
        const hasSavedKey = apiKeyInput.placeholder.includes('已设置');

        if (!apiKey && !hasSavedKey) {
            this.showTestResult(resultEl, '请先输入 Unsplash Access Key', 'error');
            return;
        }

        btn.disabled = true;
        btn.textContent = '测试中...';

        // 如果输入框为空但有已保存的key，显示提示
        if (!apiKey && hasSavedKey) {
            this.showTestResult(resultEl, '💡 使用已保存的 Access Key 进行测试...', 'info');
        } else {
            this.showTestResult(resultEl, '正在测试 API...', 'info');
        }

        try {
            // 发送apiKey，如果为空，后端将使用已保存的配置
            const result = await api.testUnsplash(apiKey || '');

            if (result.success) {
                this.showTestResult(resultEl, `✓ 测试成功！找到图片：${result.image_url}`, 'success');
                toast.success('Unsplash API 测试成功');
            } else {
                this.showTestResult(resultEl, `✗ 测试失败：${result.error}`, 'error');
                toast.error('Unsplash API 测试失败');
            }
        } catch (error) {
            this.showTestResult(resultEl, `✗ 测试失败：${error.message}`, 'error');
            toast.error('Unsplash API 测试失败');
        } finally {
            btn.disabled = false;
            btn.textContent = '测试 Unsplash API';
        }
    }

    /**
     * 测试 Pexels API
     */
    async testPexels() {
        const apiKeyInput = document.getElementById('pexelsKey');
        const apiKey = apiKeyInput.value.trim();
        const resultEl = document.getElementById('pexelsTestResult');
        const btn = document.getElementById('testPexels');

        // 检查是否有已保存的配置（通过placeholder判断）
        const hasSavedKey = apiKeyInput.placeholder.includes('已设置');

        if (!apiKey && !hasSavedKey) {
            this.showTestResult(resultEl, '请先输入 Pexels API Key', 'error');
            return;
        }

        btn.disabled = true;
        btn.textContent = '测试中...';

        // 如果输入框为空但有已保存的key，显示提示
        if (!apiKey && hasSavedKey) {
            this.showTestResult(resultEl, '💡 使用已保存的 API Key 进行测试...', 'info');
        } else {
            this.showTestResult(resultEl, '正在测试 API...', 'info');
        }

        try {
            // 发送apiKey，如果为空，后端将使用已保存的配置
            const result = await api.testPexels(apiKey || '');

            if (result.success) {
                this.showTestResult(resultEl, `✓ 测试成功！找到图片：${result.image_url}`, 'success');
                toast.success('Pexels API 测试成功');
            } else {
                this.showTestResult(resultEl, `✗ 测试失败：${result.error}`, 'error');
                toast.error('Pexels API 测试失败');
            }
        } catch (error) {
            this.showTestResult(resultEl, `✗ 测试失败：${error.message}`, 'error');
            toast.error('Pexels API 测试失败');
        } finally {
            btn.disabled = false;
            btn.textContent = '测试 Pexels API';
        }
    }

    /**
     * 测试 Pixabay API
     */
    async testPixabay() {
        const apiKeyInput = document.getElementById('pixabayKey');
        const apiKey = apiKeyInput.value.trim();
        const resultEl = document.getElementById('pixabayTestResult');
        const btn = document.getElementById('testPixabay');

        // 检查是否有已保存的配置（通过placeholder判断）
        const hasSavedKey = apiKeyInput.placeholder.includes('已设置');

        if (!apiKey && !hasSavedKey) {
            this.showTestResult(resultEl, '请先输入 Pixabay API Key', 'error');
            return;
        }

        btn.disabled = true;
        btn.textContent = '测试中...';

        // 如果输入框为空但有已保存的key，显示提示
        if (!apiKey && hasSavedKey) {
            this.showTestResult(resultEl, '💡 使用已保存的 API Key 进行测试...', 'info');
        } else {
            this.showTestResult(resultEl, '正在测试 API...', 'info');
        }

        try {
            // 发送apiKey，如果为空，后端将使用已保存的配置
            const result = await api.testPixabay(apiKey || '');

            if (result.success) {
                this.showTestResult(resultEl, `✓ 测试成功！找到图片：${result.image_url}`, 'success');
                toast.success('Pixabay API 测试成功');
            } else {
                this.showTestResult(resultEl, `✗ 测试失败：${result.error}`, 'error');
                toast.error('Pixabay API 测试失败');
            }
        } catch (error) {
            this.showTestResult(resultEl, `✗ 测试失败：${error.message}`, 'error');
            toast.error('Pixabay API 测试失败');
        } finally {
            btn.disabled = false;
            btn.textContent = '测试 Pixabay API';
        }
    }

    /**
     * 测试主模型
     */
    async testDefaultModel() {
        const modelName = document.getElementById('defaultModel').value;
        const apiKey = document.getElementById('geminiApiKey').value || '';
        const baseUrl = document.getElementById('geminiBaseUrl').value || 'https://generativelanguage.googleapis.com';
        const resultEl = document.getElementById('defaultModelTestResult');

        if (!modelName) {
            this.showTestResult(resultEl, '请先选择模型', 'error');
            return;
        }

        const btn = document.getElementById('testDefaultModel');
        btn.disabled = true;
        btn.textContent = '测试中...';
        this.showTestResult(resultEl, '正在测试模型...', 'info');

        try {
            const result = await api.testModel(modelName, apiKey, baseUrl);

            if (result.success) {
                this.showTestResult(resultEl, `✓ ${result.message}\n回复: ${result.reply}`, 'success');
                toast.success('模型测试成功');
            } else {
                this.showTestResult(resultEl, `✗ ${result.error}`, 'error');
                toast.error('模型测试失败');
            }
        } catch (error) {
            this.showTestResult(resultEl, `✗ 测试失败：${error.message}`, 'error');
            toast.error('模型测试失败');
        } finally {
            btn.disabled = false;
            btn.textContent = '测试主模型';
        }
    }

    /**
     * 测试摘要模型
     */
    async testSummaryModel() {
        const modelName = document.getElementById('comfyuiSummaryModel').value;
        const resultEl = document.getElementById('summaryModelTestResult');

        if (!modelName || modelName === '__default__') {
            this.showTestResult(resultEl, '请先选择具体的摘要模型（不能选择"使用主写作模型"）', 'error');
            return;
        }

        const apiKey = document.getElementById('geminiApiKey').value || '';
        const baseUrl = document.getElementById('geminiBaseUrl').value || 'https://generativelanguage.googleapis.com';

        const btn = document.getElementById('testSummaryModel');
        btn.disabled = true;
        btn.textContent = '测试中...';
        this.showTestResult(resultEl, '正在测试模型...', 'info');

        try {
            const result = await api.testModel(modelName, apiKey, baseUrl);

            if (result.success) {
                this.showTestResult(resultEl, `✓ ${result.message}\n回复: ${result.reply}`, 'success');
                toast.success('摘要模型测试成功');
            } else {
                this.showTestResult(resultEl, `✗ ${result.error}`, 'error');
                toast.error('摘要模型测试失败');
            }
        } catch (error) {
            this.showTestResult(resultEl, `✗ 测试失败：${error.message}`, 'error');
            toast.error('摘要模型测试失败');
        } finally {
            btn.disabled = false;
            btn.textContent = '测试摘要模型';
        }
    }

    /**
     * 测试 ComfyUI
     */
    async testComfyUI() {
        const comfyuiEnabled = document.getElementById('comfyuiEnabled').checked;
        const comfyuiServerUrl = document.getElementById('comfyuiServerUrl').value.trim();
        const comfyuiWorkflowPath = document.getElementById('comfyuiWorkflowPath').value.trim();
        const comfyuiPositiveStyle = document.getElementById('comfyuiPositiveStyle')?.value.trim() || '';
        const comfyuiNegativeStyle = document.getElementById('comfyuiNegativeStyle')?.value.trim() || '';
        const resultEl = document.getElementById('comfyuiTestResult');

        if (!comfyuiWorkflowPath) {
            this.showTestResult(resultEl, '请先配置 Workflow JSON 路径', 'error');
            return;
        }

        const settings = {
            enabled: comfyuiEnabled,
            server_url: comfyuiServerUrl || 'http://127.0.0.1:8188',
            workflow_path: comfyuiWorkflowPath
        };

        const btn = document.getElementById('testComfyui');
        btn.disabled = true;
        btn.textContent = '测试中...';
        this.showTestResult(resultEl, '正在调用 ComfyUI...', 'info');

        try {
            const result = await api.testComfyUI({
                comfyui_settings: settings,
                comfyui_positive_style: comfyuiPositiveStyle,
                comfyui_negative_style: comfyuiNegativeStyle
            });

            if (result.success) {
                const path = result.image_path || '已生成图片';
                this.showTestResult(resultEl, `✓ 测试成功！输出文件：${path}`, 'success');
                toast.success('ComfyUI 测试成功');
            } else {
                this.showTestResult(resultEl, `✗ 测试失败：${result.error}`, 'error');
                toast.error('ComfyUI 测试失败');
            }
        } catch (error) {
            this.showTestResult(resultEl, `✗ 测试失败：${error.message}`, 'error');
            toast.error('ComfyUI 测试失败');
        } finally {
            btn.disabled = false;
            btn.textContent = '测试 ComfyUI 工作流';
        }
    }

    /**
     * 测试 Gemini 图像生成 API
     */
    async testGeminiImage() {
        const resultEl = document.getElementById('geminiImageTestResult');
        const btn = document.getElementById('testGeminiImage');

        // 防止重复点击
        if (btn.disabled) {
            console.log('测试正在进行中，请勿重复点击');
            return;
        }

        // 获取配置（可以留空，后端会使用已保存的配置）
        const apiKey = document.getElementById('geminiImageApiKey').value.trim();
        const baseUrl = document.getElementById('geminiImageBaseUrl').value.trim();
        const model = document.getElementById('geminiImageModel').value;

        btn.disabled = true;
        btn.textContent = '测试中...';

        // 显示使用的配置来源
        if (!apiKey && !baseUrl) {
            this.showTestResult(resultEl, '💡 使用已保存的配置进行测试...', 'info');
        } else if (!apiKey) {
            this.showTestResult(resultEl, '💡 API Key 使用已保存配置，Base URL 使用当前输入...', 'info');
        } else if (!baseUrl) {
            this.showTestResult(resultEl, '💡 API Key 使用当前输入，Base URL 使用已保存配置...', 'info');
        } else {
            this.showTestResult(resultEl, '正在使用当前输入的配置进行测试...', 'info');
        }

        try {
            const result = await api.testGeminiImage(apiKey || null, baseUrl || null, model);

            if (result.success) {
                this.showTestResult(resultEl, `✓ ${result.message}\n图片路径: ${result.image_path}`, 'success');
                toast.success('Gemini 图像生成测试成功');
            } else {
                // 特殊处理 401 错误
                if (result.message && result.message.includes('Access denied')) {
                    this.showTestResult(
                        resultEl,
                        `✗ API Key 验证失败\n\n可能原因：\n1. API Key 无效或已过期\n2. 当前模型 (${model}) 不支持图像生成\n3. 需要使用支持 Imagen API 的代理服务\n\n建议：检查 API Key 或使用 ComfyUI 本地生成`,
                        'error'
                    );
                } else {
                    this.showTestResult(resultEl, `✗ 测试失败：${result.message}`, 'error');
                }
                toast.error('Gemini 图像生成测试失败');
            }
        } catch (error) {
            const errorMsg = error.message || error.data?.message || JSON.stringify(error);
            this.showTestResult(resultEl, `✗ 测试失败：${errorMsg}`, 'error');
            toast.error('Gemini 图像生成测试失败');
        } finally {
            // 确保按钮状态恢复
            setTimeout(() => {
                btn.disabled = false;
                btn.textContent = '测试生成';
            }, 100);
        }
    }

    /**
     * 加载 Gemini 图像生成模型列表
     */
    async loadGeminiImageModels() {
        const selectEl = document.getElementById('geminiImageModel');
        const btn = document.getElementById('loadGeminiImageModels');

        btn.disabled = true;
        btn.textContent = '加载中...';

        try {
            // 用户点击刷新按钮，应该强制从API获取最新列表
            const result = await api.getGeminiImageModels(true);

            if (result.models && result.models.length > 0) {
                const currentValue = selectEl.value;
                selectEl.innerHTML = '';

                result.models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model.id;
                    option.textContent = `${model.name}${model.description ? ' - ' + model.description : ''}`;
                    selectEl.appendChild(option);
                });

                // 恢复之前的选择
                if (currentValue && Array.from(selectEl.options).some(opt => opt.value === currentValue)) {
                    selectEl.value = currentValue;
                }

                toast.success('模型列表加载成功');
            } else {
                toast.info('未找到可用模型，使用默认列表');
            }
        } catch (error) {
            console.error('加载模型列表失败:', error);
            toast.error('加载模型列表失败: ' + (error.message || error));
        } finally {
            btn.disabled = false;
            btn.textContent = '刷新列表';
        }
    }

    /**
     * 显示测试结果
     */
    showTestResult(element, message, type) {
        if (!element) return;

        element.textContent = message;
        element.className = `test-result ${type}`;
        element.style.display = 'block';
    }
}

// 导出到全局
window.APITester = APITester;
