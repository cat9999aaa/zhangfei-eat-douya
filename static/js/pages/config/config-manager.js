/**
 * 配置管理器
 * 负责配置的加载、保存、应用
 */

class ConfigManager {
    constructor() {
        this.currentConfig = null;
        this.comfyuiDefaults = {
            enabled: true,
            server_url: 'http://127.0.0.1:8188',
            queue_size: 2,
            timeout_seconds: 180,
            max_attempts: 2,
            seed: -1,
            workflow_path: ''
        };
        this.geminiImageDefaults = {
            enabled: true,
            api_key: '',
            base_url: '',
            model: 'imagen-3.0-generate-001',
            style: 'realistic',
            aspect_ratio: '16:9',
            custom_prefix: '',
            custom_suffix: '',
            max_retries: 3,
            timeout: 30
        };
    }

    /**
     * 加载配置
     */
    async loadConfig() {
        try {
            const config = await api.getConfig();
            this.currentConfig = config;

            // 应用到UI
            this.applyToUI(config);

            return config;
        } catch (error) {
            console.error('加载配置失败:', error);
            toast.error('加载配置失败');
            throw error;
        }
    }

    /**
     * 应用配置到UI
     */
    applyToUI(config) {
        const elements = this.getFormElements();

        // Gemini API 配置
        if (config.gemini_api_key_set) {
            elements.geminiApiKey.placeholder = '已设置 API Key（如需更换请重新输入）';
        }
        if (config.gemini_base_url) {
            elements.geminiBaseUrl.value = config.gemini_base_url;
        }

        // 图片API配置
        if (config.unsplash_access_key_set) {
            elements.unsplashKey.placeholder = '已设置 Access Key（如需更换请重新输入）';
        }
        if (config.pexels_api_key_set) {
            elements.pexelsKey.placeholder = '已设置 API Key（如需更换请重新输入）';
        }
        if (config.pixabay_api_key_set) {
            elements.pixabayKey.placeholder = '已设置 API Key（如需更换请重新输入）';
        }

        // Pandoc 和输出目录
        if (config.pandoc_path) {
            elements.pandocPath.value = config.pandoc_path;
        }
        if (config.output_directory) {
            elements.outputDirectory.value = config.output_directory;
        }

        // 提示词和并发数
        if (config.default_prompt) {
            elements.defaultPrompt.value = config.default_prompt;
        }
        if (config.max_concurrent_tasks) {
            elements.maxConcurrentTasks.value = config.max_concurrent_tasks;
        }
        if (config.max_retry_attempts !== undefined) {
            elements.maxRetryAttempts.value = config.max_retry_attempts;
        }

        // Temperature 和 Top-P
        if (config.temperature !== undefined) {
            elements.temperature.value = config.temperature;
        }
        if (config.top_p !== undefined) {
            elements.topP.value = config.top_p;
        }

        // Google 搜索和引用设置
        if (config.enable_google_search !== undefined) {
            elements.enableGoogleSearch.checked = config.enable_google_search;
            this.updateToggleStatus('enableGoogleSearch', config.enable_google_search);
        }
        if (config.append_citations !== undefined) {
            elements.appendCitations.checked = config.append_citations;
            this.updateToggleStatus('appendCitations', config.append_citations);
        }

        // ComfyUI 配置
        this.applyComfyuiSettings(config.comfyui_settings);

        // 图片数量
        if (config.comfyui_image_count) {
            elements.comfyuiImageCount.value = config.comfyui_image_count;
        }

        // 风格模板
        if (config.comfyui_style_templates) {
            this.loadStyleTemplates(config.comfyui_style_templates, config.comfyui_style_template);
        }

        // 自定义风格
        if (config.comfyui_positive_style) {
            elements.comfyuiPositiveStyle.value = config.comfyui_positive_style;
        }
        if (config.comfyui_negative_style) {
            elements.comfyuiNegativeStyle.value = config.comfyui_negative_style;
        }

        // 摘要模型
        if (config.comfyui_summary_model) {
            elements.comfyuiSummaryModel.value = config.comfyui_summary_model;
        }

        // Gemini 图像生成配置
        this.applyGeminiImageSettings(
            config.gemini_image_settings,
            config.gemini_image_api_key_set,
            config.gemini_image_base_url_set
        );
    }

    /**
     * 应用 ComfyUI 设置
     */
    applyComfyuiSettings(settings = {}) {
        const elements = this.getFormElements();
        const merged = { ...this.comfyuiDefaults, ...settings };

        elements.comfyuiEnabled.checked = !!merged.enabled;
        elements.comfyuiServerUrl.value = merged.server_url || this.comfyuiDefaults.server_url;
        elements.comfyuiWorkflowPath.value = merged.workflow_path || '';
    }

    /**
     * 收集 ComfyUI 设置
     */
    collectComfyuiSettings() {
        const elements = this.getFormElements();

        return {
            ...this.comfyuiDefaults,
            enabled: elements.comfyuiEnabled.checked,
            server_url: elements.comfyuiServerUrl.value.trim() || this.comfyuiDefaults.server_url,
            workflow_path: elements.comfyuiWorkflowPath.value.trim() || ''
        };
    }

    /**
     * 应用 Gemini 图像设置
     */
    applyGeminiImageSettings(settings = {}, apiKeySet = false, baseUrlSet = false) {
        const elements = this.getFormElements();
        const merged = { ...this.geminiImageDefaults, ...settings };

        elements.geminiImageEnabled.checked = !!merged.enabled;

        // API Key placeholder 显示逻辑
        if (apiKeySet) {
            elements.geminiImageApiKey.placeholder = '已设置独立 API Key（如需更换请重新输入）';
        } else if (this.currentConfig && this.currentConfig.gemini_api_key_set) {
            elements.geminiImageApiKey.placeholder = '留空则使用通用 Gemini API Key（已配置）';
        } else {
            elements.geminiImageApiKey.placeholder = '留空则使用通用 Gemini API Key（未配置）';
        }

        // Base URL 显示逻辑
        // 如果有独立配置，显示独立配置的值；否则留空（让 placeholder 显示提示）
        if (baseUrlSet && merged.base_url) {
            elements.geminiImageBaseUrl.value = merged.base_url;
        } else {
            elements.geminiImageBaseUrl.value = '';
        }

        // Base URL placeholder 显示逻辑
        if (baseUrlSet) {
            elements.geminiImageBaseUrl.placeholder = '已设置独立 Base URL（如需更换请重新输入）';
        } else if (this.currentConfig && this.currentConfig.gemini_base_url) {
            elements.geminiImageBaseUrl.placeholder = `留空则使用通用配置（当前：${this.currentConfig.gemini_base_url}）`;
        } else {
            elements.geminiImageBaseUrl.placeholder = '留空则使用通用 Gemini Base URL';
        }

        // 注意：模型值由 initGeminiImageModelSelect() 方法设置
        // 因为需要先初始化下拉框选项，再设置值
        // elements.geminiImageModel.value = merged.model || 'imagen-3.0-generate-001';

        elements.geminiImageStyle.value = merged.style || 'realistic';
        elements.geminiImageAutoDetect.checked = merged.auto_detect_topic !== false; // 默认开启
        elements.geminiImageEthnicity.value = merged.ethnicity || 'auto';
        elements.geminiImageAspectRatio.value = merged.aspect_ratio || '16:9';
        elements.geminiImageCustomPrefix.value = merged.custom_prefix || '';
        elements.geminiImageCustomSuffix.value = merged.custom_suffix || '';
        elements.geminiImageMaxRetries.value = merged.max_retries || 3;
        elements.geminiImageTimeout.value = merged.timeout || 30;
    }

    /**
     * 收集 Gemini 图像设置
     */
    collectGeminiImageSettings() {
        const elements = this.getFormElements();

        const settings = {
            enabled: elements.geminiImageEnabled.checked,
            base_url: elements.geminiImageBaseUrl.value.trim() || '',
            model: elements.geminiImageModel.value || 'imagen-3.0-generate-001',
            style: elements.geminiImageStyle.value || 'realistic',
            auto_detect_topic: elements.geminiImageAutoDetect.checked,
            ethnicity: elements.geminiImageEthnicity.value || 'auto',
            aspect_ratio: elements.geminiImageAspectRatio.value || '16:9',
            custom_prefix: elements.geminiImageCustomPrefix.value.trim() || '',
            custom_suffix: elements.geminiImageCustomSuffix.value.trim() || '',
            max_retries: parseInt(elements.geminiImageMaxRetries.value) || 3,
            timeout: parseInt(elements.geminiImageTimeout.value) || 30
        };

        // 如果用户输入了新的 API Key
        if (elements.geminiImageApiKey.value) {
            settings.api_key = elements.geminiImageApiKey.value;
        }

        return settings;
    }

    /**
     * 加载风格模板下拉选项
     */
    loadStyleTemplates(templates, selectedValue) {
        const elements = this.getFormElements();
        elements.comfyuiStyleTemplate.innerHTML = '';

        templates.forEach(template => {
            const option = document.createElement('option');
            option.value = template.id;
            option.textContent = template.label;
            elements.comfyuiStyleTemplate.appendChild(option);
        });

        if (selectedValue) {
            elements.comfyuiStyleTemplate.value = selectedValue;
        }

        this.toggleCustomStyleBlocks();
    }

    /**
     * 切换自定义风格块显示
     */
    toggleCustomStyleBlocks() {
        const elements = this.getFormElements();
        const customBlocks = document.querySelectorAll('.custom-style-block');
        const isCustom = elements.comfyuiStyleTemplate.value === 'custom';

        customBlocks.forEach(block => {
            block.style.display = isCustom ? 'block' : 'none';
        });
    }

    /**
     * 更新开关状态文本
     */
    updateToggleStatus(fieldId, isEnabled) {
        const statusElement = document.getElementById(`${fieldId}Status`);
        if (statusElement) {
            statusElement.textContent = isEnabled ? '已启用' : '已禁用';
        }
    }

    /**
     * 保存配置
     */
    async saveConfig(imageDirs = [], imagePriority = []) {
        const elements = this.getFormElements();

        const newConfig = {
            gemini_base_url: elements.geminiBaseUrl.value || 'https://generativelanguage.googleapis.com',
            pandoc_path: elements.pandocPath.value,
            output_directory: elements.outputDirectory.value || 'output',
            default_model: elements.defaultModel.value,
            default_prompt: elements.defaultPrompt.value,
            temperature: parseFloat(elements.temperature.value) || 1.0,
            top_p: parseFloat(elements.topP.value) || 0.95,
            enable_google_search: elements.enableGoogleSearch.checked,
            append_citations: elements.appendCitations.checked,
            max_concurrent_tasks: parseInt(elements.maxConcurrentTasks.value) || 3,
            max_retry_attempts: parseInt(elements.maxRetryAttempts.value) || 10,
            comfyui_settings: this.collectComfyuiSettings(),
            comfyui_image_count: parseInt(elements.comfyuiImageCount.value) || 1,
            comfyui_style_template: elements.comfyuiStyleTemplate.value || 'custom',
            comfyui_positive_style: elements.comfyuiPositiveStyle.value.trim() || '',
            comfyui_negative_style: elements.comfyuiNegativeStyle.value.trim() || '',
            comfyui_summary_model: elements.comfyuiSummaryModel.value || '__default__',
            gemini_image_settings: this.collectGeminiImageSettings(),
            local_image_directories: imageDirs,
            image_source_priority: imagePriority
        };

        // 只在用户输入了新值时添加
        if (elements.geminiApiKey.value) {
            newConfig.gemini_api_key = elements.geminiApiKey.value;
        }
        if (elements.unsplashKey.value) {
            newConfig.unsplash_access_key = elements.unsplashKey.value;
        }
        if (elements.pexelsKey.value) {
            newConfig.pexels_api_key = elements.pexelsKey.value;
        }
        if (elements.pixabayKey.value) {
            newConfig.pixabay_api_key = elements.pixabayKey.value;
        }

        try {
            await api.saveConfig(newConfig);
            toast.success('配置保存成功！');

            // 重新加载配置
            await this.loadConfig();

            // 清空敏感输入框
            elements.geminiApiKey.value = '';
            elements.unsplashKey.value = '';
            elements.pexelsKey.value = '';
            elements.pixabayKey.value = '';
            elements.geminiImageApiKey.value = '';

            return true;
        } catch (error) {
            toast.error('配置保存失败: ' + error.message);
            return false;
        }
    }

    /**
     * 重置配置
     */
    resetConfig() {
        const elements = this.getFormElements();

        elements.geminiApiKey.value = '';
        elements.geminiBaseUrl.value = 'https://generativelanguage.googleapis.com';
        elements.unsplashKey.value = '';
        elements.pexelsKey.value = '';
        elements.pixabayKey.value = '';
        elements.pandocPath.value = '';
        elements.outputDirectory.value = 'output';
        elements.defaultModel.value = 'gemini-pro';
        elements.defaultPrompt.value = '';
        elements.temperature.value = 1.0;
        elements.topP.value = 0.95;
        elements.enableGoogleSearch.checked = true;
        this.updateToggleStatus('enableGoogleSearch', true);
        elements.appendCitations.checked = false;
        this.updateToggleStatus('appendCitations', false);
        elements.maxConcurrentTasks.value = 3;
        elements.maxRetryAttempts.value = 10;

        this.applyComfyuiSettings(this.comfyuiDefaults);

        elements.comfyuiImageCount.value = 1;
        elements.comfyuiStyleTemplate.value = 'custom';
        elements.comfyuiPositiveStyle.value = '';
        elements.comfyuiNegativeStyle.value = '';
        elements.comfyuiSummaryModel.value = '__default__';

        // Gemini 图像配置
        this.applyGeminiImageSettings(this.geminiImageDefaults);

        this.toggleCustomStyleBlocks();

        toast.info('已重置为默认值（尚未保存）');
    }

    /**
     * 加载模型列表
     */
    async loadModels(preferredModel = null, forceRefresh = false) {
        const elements = this.getFormElements();

        try {
            // 从缓存或 API 获取模型列表
            const data = await api.getModels(forceRefresh);
            const models = Array.isArray(data.models) ? data.models : [];
            const previousSelection = preferredModel || elements.defaultModel.value;

            if (models.length === 0) {
                // 如果没有模型，保留默认选项
                if (elements.defaultModel.options.length === 0) {
                    elements.defaultModel.innerHTML = '<option value="gemini-pro">gemini-pro</option>';
                }
                return;
            }

            elements.defaultModel.innerHTML = '';

            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.name;
                option.textContent = model.display_name || model.name;
                elements.defaultModel.appendChild(option);
            });

            // 恢复之前的选择
            if (previousSelection && models.some(m => m.name === previousSelection)) {
                elements.defaultModel.value = previousSelection;
            } else if (elements.defaultModel.options.length > 0) {
                elements.defaultModel.selectedIndex = 0;
            }

            if (data.from_cache) {
                console.log(`✓ 主模型列表已从缓存加载 (${models.length} 个模型, 上次更新: ${data.last_updated})`);
            } else if (forceRefresh) {
                console.log(`✓ 主模型列表已刷新 (${models.length} 个模型)`);
            } else {
                console.log(`✓ 主模型列表已加载 (${models.length} 个模型)`);
            }
        } catch (error) {
            console.error('加载模型列表失败:', error);
            if (elements.defaultModel.options.length === 0) {
                elements.defaultModel.innerHTML = '<option value="gemini-pro">gemini-pro (加载列表失败)</option>';
            }
        }
    }

    /**
     * 加载摘要模型列表
     */
    async loadSummaryModels(preferredModel = null, forceRefresh = false) {
        const elements = this.getFormElements();
        const currentModel = preferredModel || elements.comfyuiSummaryModel.value;

        try {
            // 支持强制刷新，从 API 或缓存获取模型列表
            const data = await api.getModels(forceRefresh);
            elements.comfyuiSummaryModel.innerHTML = '';

            // 添加所有可用模型（移除"使用主写作模型"选项，让用户独立选择）
            data.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.name;
                option.textContent = model.display_name || model.name;
                elements.comfyuiSummaryModel.appendChild(option);
            });

            // 恢复之前选中的模型
            if (currentModel && currentModel !== '__default__') {
                const modelExists = Array.from(elements.comfyuiSummaryModel.options).some(opt => opt.value === currentModel);
                if (modelExists) {
                    elements.comfyuiSummaryModel.value = currentModel;
                }
            }

            if (data.from_cache) {
                console.log(`✓ 摘要模型列表已从缓存加载 (${data.models.length} 个模型, 上次更新: ${data.last_updated})`);
            } else {
                console.log(`✓ 摘要模型列表已从 API 加载 (${data.models.length} 个模型)`);
            }
        } catch (error) {
            console.error('加载摘要模型列表失败:', error);
            elements.comfyuiSummaryModel.innerHTML = '<option value="">加载失败</option>';
        }
    }

    /**
     * 获取表单元素
     */
    getFormElements() {
        return {
            geminiApiKey: document.getElementById('geminiApiKey'),
            geminiBaseUrl: document.getElementById('geminiBaseUrl'),
            unsplashKey: document.getElementById('unsplashKey'),
            pexelsKey: document.getElementById('pexelsKey'),
            pixabayKey: document.getElementById('pixabayKey'),
            pandocPath: document.getElementById('pandocPath'),
            outputDirectory: document.getElementById('outputDirectory'),
            defaultModel: document.getElementById('defaultModel'),
            defaultPrompt: document.getElementById('defaultPrompt'),
            temperature: document.getElementById('temperature'),
            topP: document.getElementById('topP'),
            maxConcurrentTasks: document.getElementById('maxConcurrentTasks'),
            maxRetryAttempts: document.getElementById('maxRetryAttempts'),
            enableGoogleSearch: document.getElementById('enableGoogleSearch'),
            appendCitations: document.getElementById('appendCitations'),
            comfyuiEnabled: document.getElementById('comfyuiEnabled'),
            comfyuiServerUrl: document.getElementById('comfyuiServerUrl'),
            comfyuiWorkflowPath: document.getElementById('comfyuiWorkflowPath'),
            comfyuiImageCount: document.getElementById('comfyuiImageCount'),
            comfyuiStyleTemplate: document.getElementById('comfyuiStyleTemplate'),
            comfyuiPositiveStyle: document.getElementById('comfyuiPositiveStyle'),
            comfyuiNegativeStyle: document.getElementById('comfyuiNegativeStyle'),
            comfyuiSummaryModel: document.getElementById('comfyuiSummaryModel'),
            geminiImageEnabled: document.getElementById('geminiImageEnabled'),
            geminiImageApiKey: document.getElementById('geminiImageApiKey'),
            geminiImageBaseUrl: document.getElementById('geminiImageBaseUrl'),
            geminiImageModel: document.getElementById('geminiImageModel'),
            geminiImageStyle: document.getElementById('geminiImageStyle'),
            geminiImageAutoDetect: document.getElementById('geminiImageAutoDetect'),
            geminiImageEthnicity: document.getElementById('geminiImageEthnicity'),
            geminiImageAspectRatio: document.getElementById('geminiImageAspectRatio'),
            geminiImageCustomPrefix: document.getElementById('geminiImageCustomPrefix'),
            geminiImageCustomSuffix: document.getElementById('geminiImageCustomSuffix'),
            geminiImageMaxRetries: document.getElementById('geminiImageMaxRetries'),
            geminiImageTimeout: document.getElementById('geminiImageTimeout')
        };
    }
}

// 导出到全局
window.ConfigManager = ConfigManager;
