/**
 * 配置页面主入口
 * 负责初始化所有模块并协调它们的交互
 */

class ConfigPageApp {
    constructor() {
        this.initialized = false;
    }

    /**
     * 初始化应用
     */
    async init() {
        if (this.initialized) return;

        // 初始化 Tab 管理器
        const tabsContainer = document.querySelector('.tabs-container');
        if (tabsContainer) {
            this.tabManager = new TabManager(tabsContainer);
        }

        // 初始化配置管理器
        this.configManager = new ConfigManager();

        // 初始化 API 测试器
        this.apiTester = new APITester();

        // 初始化图片目录管理器
        const imageDirsContainer = document.getElementById('localImageDirs');
        if (imageDirsContainer) {
            this.imageDirManager = new ImageDirectoryManager(imageDirsContainer);
        }

        // 初始化优先级排序器
        const priorityList = document.getElementById('imagePriorityList');
        if (priorityList) {
            this.prioritySorter = new PrioritySorter(priorityList);
            await this.prioritySorter.loadPriority();
        }

        // 加载配置
        await this.loadConfig();

        // 绑定事件
        this.bindEvents();

        this.initialized = true;
        console.log('配置页面初始化完成');
    }

    /**
     * 加载配置
     */
    async loadConfig() {
        try {
            const config = await this.configManager.loadConfig();

            // 加载模型列表
            await this.configManager.loadModels(config.default_model);

            // 加载摘要模型列表，传入配置中保存的模型值
            await this.configManager.loadSummaryModels(config.comfyui_summary_model);

            // 初始化 Gemini 图像模型下拉框
            // 先设置当前保存的模型名称，避免显示为空
            this.initGeminiImageModelSelect(config);

            // 加载图片目录
            if (this.imageDirManager && config.local_image_directories) {
                this.imageDirManager.loadDirectories(config.local_image_directories);
            }

            toast.success('配置加载成功');
        } catch (error) {
            console.error('加载配置失败:', error);
        }
    }

    /**
     * 初始化 Gemini 图像模型下拉框
     * 从缓存加载模型列表，如果没有缓存则只显示当前保存的模型
     */
    async initGeminiImageModelSelect(config) {
        const modelSelect = document.getElementById('geminiImageModel');
        if (!modelSelect) return;

        const currentModel = config.gemini_image_settings?.model || 'gemini-2.5-flash-image-preview';

        try {
            // 从缓存加载模型列表（不强制刷新）
            const data = await api.getGeminiImageModels(false);

            if (data.models && data.models.length > 0) {
                // 有缓存数据，加载完整的模型列表
                modelSelect.innerHTML = '';
                data.models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model.id;
                    option.textContent = model.name;
                    if (model.description) {
                        option.title = model.description;
                    }
                    modelSelect.appendChild(option);
                });

                // 检查当前模型是否在列表中
                const modelExists = Array.from(modelSelect.options).some(opt => opt.value === currentModel);
                if (!modelExists && currentModel) {
                    // 如果不在列表中，添加为一个选项
                    const option = document.createElement('option');
                    option.value = currentModel;
                    option.textContent = `${currentModel} (当前配置)`;
                    modelSelect.insertBefore(option, modelSelect.firstChild);
                }

                // 设置当前值
                modelSelect.value = currentModel;

                if (data.from_cache) {
                    console.log(`✓ Gemini 图像模型已从缓存加载 (${data.models.length} 个模型, 上次更新: ${data.last_updated})`);
                } else {
                    console.log(`✓ Gemini 图像模型已加载 (${data.models.length} 个模型)`);
                }
            } else {
                // 没有缓存，只添加当前模型
                modelSelect.innerHTML = '';
                const option = document.createElement('option');
                option.value = currentModel;
                option.textContent = currentModel;
                modelSelect.appendChild(option);
                modelSelect.value = currentModel;

                console.log(`✓ Gemini 图像模型已初始化: ${currentModel}`);
                console.log(`💡 提示: 点击"刷新列表"按钮可从服务器获取最新的可用模型列表`);
            }
        } catch (error) {
            // 加载失败，只添加当前模型
            console.warn('加载 Gemini 图像模型缓存失败:', error);
            modelSelect.innerHTML = '';
            const option = document.createElement('option');
            option.value = currentModel;
            option.textContent = currentModel;
            modelSelect.appendChild(option);
            modelSelect.value = currentModel;
        }
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 保存配置按钮
        const saveBtn = document.getElementById('saveConfig');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.handleSave());
        }

        // 重置配置按钮
        const resetBtn = document.getElementById('resetConfig');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.handleReset());
        }

        // 风格模板变化时切换自定义块显示
        const styleTemplate = document.getElementById('comfyuiStyleTemplate');
        if (styleTemplate) {
            styleTemplate.addEventListener('change', () => {
                this.configManager.toggleCustomStyleBlocks();
            });
        }

        // 刷新主模型列表按钮
        const refreshDefaultModelsBtn = document.getElementById('refreshDefaultModels');
        if (refreshDefaultModelsBtn) {
            refreshDefaultModelsBtn.addEventListener('click', () => this.handleRefreshDefaultModels());
        }

        // 刷新摘要模型列表按钮
        const refreshSummaryModelsBtn = document.getElementById('refreshSummaryModels');
        if (refreshSummaryModelsBtn) {
            refreshSummaryModelsBtn.addEventListener('click', () => this.handleRefreshSummaryModels());
        }

        // Gemini 图像生成相关按钮
        const loadGeminiImageModelsBtn = document.getElementById('loadGeminiImageModels');
        if (loadGeminiImageModelsBtn) {
            loadGeminiImageModelsBtn.addEventListener('click', () => this.handleLoadGeminiImageModels());
        }

        const testGeminiImageBtn = document.getElementById('testGeminiImage');
        if (testGeminiImageBtn) {
            testGeminiImageBtn.addEventListener('click', () => this.handleTestGeminiImage());
        }
    }

    /**
     * 处理加载 Gemini 图像模型列表
     */
    async handleLoadGeminiImageModels() {
        const btn = document.getElementById('loadGeminiImageModels');
        const modelSelect = document.getElementById('geminiImageModel');
        const resultDiv = document.getElementById('geminiImageTestResult');
        const apiKeyInput = document.getElementById('geminiImageApiKey');
        const baseUrlInput = document.getElementById('geminiImageBaseUrl');

        const originalText = btn.textContent;

        // 检查是否配置了必要的参数
        let apiKey = apiKeyInput.value.trim();
        let baseUrl = baseUrlInput.value.trim();

        // 如果没有输入，尝试从当前配置中获取
        if (!apiKey && this.configManager.currentConfig) {
            const settings = this.configManager.currentConfig.gemini_image_settings;
            apiKey = settings?.api_key;
        }

        if (!baseUrl && this.configManager.currentConfig) {
            const settings = this.configManager.currentConfig.gemini_image_settings;
            baseUrl = settings?.base_url;
        }

        if (!apiKey || !baseUrl) {
            resultDiv.className = 'test-result test-error';
            resultDiv.textContent = '✗ 请先配置 API Key 和 Base URL';
            resultDiv.style.display = 'block';
            toast.error('请先配置 API Key 和 Base URL');
            return;
        }

        try {
            btn.disabled = true;
            btn.textContent = '加载中...';
            resultDiv.style.display = 'none';

            // 保存当前选中的模型
            const currentModel = modelSelect.value;

            // 强制刷新，从 API 获取最新的模型列表
            const data = await api.getGeminiImageModels(true);

            // 更新模型下拉列表
            modelSelect.innerHTML = '';
            data.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = model.name;
                if (model.description) {
                    option.title = model.description;
                }
                modelSelect.appendChild(option);
            });

            // 恢复之前选中的模型
            if (currentModel) {
                // 检查当前模型是否在新列表中
                const modelExists = Array.from(modelSelect.options).some(opt => opt.value === currentModel);

                if (modelExists) {
                    modelSelect.value = currentModel;
                } else {
                    // 如果不在列表中，添加为一个选项（可能是用户自定义或旧的模型）
                    const option = document.createElement('option');
                    option.value = currentModel;
                    option.textContent = `${currentModel} (当前配置)`;
                    modelSelect.insertBefore(option, modelSelect.firstChild);
                    modelSelect.value = currentModel;
                }
            }

            resultDiv.className = 'test-result test-success';
            resultDiv.textContent = `✓ 成功加载 ${data.models.length} 个模型${currentModel ? `，已保留选择: ${currentModel}` : ''}`;
            resultDiv.style.display = 'block';

            toast.success('模型列表加载成功');
        } catch (error) {
            resultDiv.className = 'test-result test-error';
            resultDiv.textContent = `✗ 加载失败: ${error.message || error}`;
            resultDiv.style.display = 'block';
            toast.error('加载模型列表失败');
        } finally {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    }

    /**
     * 处理测试 Gemini 图像生成 API
     */
    async handleTestGeminiImage() {
        const btn = document.getElementById('testGeminiImage');
        const apiKeyInput = document.getElementById('geminiImageApiKey');
        const baseUrlInput = document.getElementById('geminiImageBaseUrl');
        const modelSelect = document.getElementById('geminiImageModel');
        const resultDiv = document.getElementById('geminiImageTestResult');

        const originalText = btn.textContent;

        // 获取输入值
        let apiKey = apiKeyInput.value.trim();
        let baseUrl = baseUrlInput.value.trim();
        const model = modelSelect.value;

        // 如果没有输入，尝试从当前配置中获取
        if (!apiKey && this.configManager.currentConfig) {
            const settings = this.configManager.currentConfig.gemini_image_settings;
            apiKey = settings?.api_key;
        }

        if (!baseUrl && this.configManager.currentConfig) {
            const settings = this.configManager.currentConfig.gemini_image_settings;
            baseUrl = settings?.base_url;
        }

        if (!apiKey || !baseUrl) {
            resultDiv.className = 'test-result test-error';
            resultDiv.textContent = '✗ 请先配置 API Key 和 Base URL';
            resultDiv.style.display = 'block';
            toast.error('请先配置 API Key 和 Base URL');
            return;
        }

        try {
            btn.disabled = true;
            btn.textContent = '测试中...';
            resultDiv.style.display = 'none';

            const data = await api.testGeminiImage(apiKey, baseUrl, model);

            if (data.success) {
                resultDiv.className = 'test-result test-success';
                resultDiv.textContent = `✓ ${data.message}`;
                toast.success('Gemini 图像生成 API 测试成功');
            } else {
                resultDiv.className = 'test-result test-error';
                resultDiv.textContent = `✗ ${data.message}`;
                toast.error('API 测试失败');
            }

            resultDiv.style.display = 'block';
        } catch (error) {
            resultDiv.className = 'test-result test-error';
            resultDiv.textContent = `✗ 测试失败: ${error.message || error}`;
            resultDiv.style.display = 'block';
            toast.error('API 测试失败');
        } finally {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    }

    /**
     * 处理刷新主模型列表
     */
    async handleRefreshDefaultModels() {
        const btn = document.getElementById('refreshDefaultModels');
        const modelSelect = document.getElementById('defaultModel');
        const originalText = btn.textContent;
        const currentModel = modelSelect.value;

        try {
            btn.disabled = true;
            btn.textContent = '刷新中...';

            // 强制刷新模型列表
            await this.configManager.loadModels(currentModel, true);

            toast.success('主模型列表刷新成功');
        } catch (error) {
            console.error('刷新主模型列表失败:', error);
            toast.error('刷新失败: ' + (error.message || error));
        } finally {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    }

    /**
     * 处理刷新摘要模型列表
     */
    async handleRefreshSummaryModels() {
        const btn = document.getElementById('refreshSummaryModels');
        const modelSelect = document.getElementById('comfyuiSummaryModel');
        const originalText = btn.textContent;
        const currentModel = modelSelect.value;

        try {
            btn.disabled = true;
            btn.textContent = '刷新中...';

            // 强制刷新摘要模型列表
            await this.configManager.loadSummaryModels(currentModel, true);

            toast.success('摘要模型列表刷新成功');
        } catch (error) {
            console.error('刷新摘要模型列表失败:', error);
            toast.error('刷新失败: ' + (error.message || error));
        } finally {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    }

    /**
     * 处理保存配置
     */
    async handleSave() {
        const saveBtn = document.getElementById('saveConfig');
        const originalText = saveBtn.textContent;

        // 获取图片目录和优先级
        const imageDirs = this.imageDirManager ? this.imageDirManager.getDirectories() : [];
        const imagePriority = this.prioritySorter ? this.prioritySorter.getPriority() : [];

        try {
            saveBtn.disabled = true;
            saveBtn.textContent = '保存中...';

            const success = await this.configManager.saveConfig(imageDirs, imagePriority);

            if (success) {
                // 重新加载配置以确保界面同步
                const config = await this.configManager.loadConfig();

                // 重新加载模型列表
                const defaultModel = document.getElementById('defaultModel').value;
                await this.configManager.loadModels(defaultModel);

                // 重新加载摘要模型列表，传入配置中保存的模型值
                await this.configManager.loadSummaryModels(config.comfyui_summary_model);

                // 重新初始化 Gemini 图像模型列表
                this.initGeminiImageModelSelect(config);

                console.log('✓ 配置已保存并重新加载');
            }
        } catch (error) {
            console.error('保存配置失败:', error);
        } finally {
            saveBtn.disabled = false;
            saveBtn.textContent = originalText;
        }
    }

    /**
     * 处理重置配置
     */
    handleReset() {
        if (!confirm('确定要重置为默认配置吗？')) {
            return;
        }

        this.configManager.resetConfig();

        // 重置图片目录
        if (this.imageDirManager) {
            this.imageDirManager.loadDirectories([]);
        }

        // 重置优先级
        if (this.prioritySorter) {
            this.prioritySorter.reorderList(['gemini_image', 'comfyui', 'user_uploaded', 'pexels', 'unsplash', 'pixabay', 'local']);
        }

        // 清除测试结果
        const testResults = document.querySelectorAll('.test-result');
        testResults.forEach(result => {
            result.style.display = 'none';
            result.textContent = '';
        });
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', async () => {
    const app = new ConfigPageApp();
    await app.init();

    // 暴露到全局，方便调试
    window.configPageApp = app;
});
