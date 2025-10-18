// DOM 元素
const geminiApiKey = document.getElementById('geminiApiKey');
const geminiBaseUrl = document.getElementById('geminiBaseUrl');
const unsplashKey = document.getElementById('unsplashKey');
const testUnsplashBtn = document.getElementById('testUnsplash');
const unsplashTestResult = document.getElementById('unsplashTestResult');
const pexelsKey = document.getElementById('pexelsKey');
const testPexelsBtn = document.getElementById('testPexels');
const pexelsTestResult = document.getElementById('pexelsTestResult');
const pixabayKey = document.getElementById('pixabayKey');
const testPixabayBtn = document.getElementById('testPixabay');
const pixabayTestResult = document.getElementById('pixabayTestResult');
const pandocPath = document.getElementById('pandocPath');
const outputDirectory = document.getElementById('outputDirectory');
const defaultModel = document.getElementById('defaultModel');
const defaultPrompt = document.getElementById('defaultPrompt');
const maxConcurrentTasks = document.getElementById('maxConcurrentTasks');
const saveConfigBtn = document.getElementById('saveConfig');
const resetConfigBtn = document.getElementById('resetConfig');
const configStatus = document.getElementById('configStatus');
const addImageDirBtn = document.getElementById('addImageDir');
const localImageDirs = document.getElementById('localImageDirs');

const comfyuiEnabled = document.getElementById('comfyuiEnabled');
const comfyuiServerUrl = document.getElementById('comfyuiServerUrl');
const comfyuiWorkflowPath = document.getElementById('comfyuiWorkflowPath');
const comfyuiImageCount = document.getElementById('comfyuiImageCount');
const comfyuiStyleTemplate = document.getElementById('comfyuiStyleTemplate');
const comfyuiPositiveStyle = document.getElementById('comfyuiPositiveStyle');
const comfyuiNegativeStyle = document.getElementById('comfyuiNegativeStyle');
const comfyuiSummaryModel = document.getElementById('comfyuiSummaryModel');
const testComfyuiBtn = document.getElementById('testComfyui');
const comfyuiTestResult = document.getElementById('comfyuiTestResult');
const testDefaultModelBtn = document.getElementById('testDefaultModel');
const defaultModelTestResult = document.getElementById('defaultModelTestResult');
const testSummaryModelBtn = document.getElementById('testSummaryModel');
const summaryModelTestResult = document.getElementById('summaryModelTestResult');

const comfyuiDefaults = {
    enabled: true,
    server_url: 'http://127.0.0.1:8188',
    queue_size: 2,
    timeout_seconds: 180,
    max_attempts: 2,
    seed: -1,
    workflow_path: ''
};

let comfyuiCurrentSettings = { ...comfyuiDefaults };

function applyComfyuiSettings(settings = {}) {
    const merged = { ...comfyuiDefaults, ...settings };
    comfyuiCurrentSettings = { ...merged };
    if (comfyuiEnabled) comfyuiEnabled.checked = !!merged.enabled;
    if (comfyuiServerUrl) comfyuiServerUrl.value = merged.server_url || comfyuiDefaults.server_url;
    if (comfyuiWorkflowPath) comfyuiWorkflowPath.value = merged.workflow_path || '';
}

function collectComfyuiSettings() {
    const base = { ...comfyuiCurrentSettings };
    base.enabled = comfyuiEnabled?.checked ?? comfyuiDefaults.enabled;
    base.server_url = comfyuiServerUrl?.value?.trim() || comfyuiDefaults.server_url;
    base.workflow_path = comfyuiWorkflowPath?.value?.trim() || '';
    return base;
}
// 页面加载时加载配置
document.addEventListener('DOMContentLoaded', () => {
    loadConfig(); // loadConfig 内部会调用 loadModels
});

// 加载配置
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        if (response.ok) {
            const config = await response.json();

            // 更新界面
            if (config.gemini_api_key_set) {
                geminiApiKey.placeholder = '已设置 API Key（如需更换请重新输入）';
            }
            if (config.gemini_base_url) {
                geminiBaseUrl.value = config.gemini_base_url;
            }
            if (config.unsplash_access_key_set) {
                unsplashKey.placeholder = '已设置 Access Key（如需更换请重新输入）';
            }
            if (pexelsKey && config.pexels_api_key_set) {
                pexelsKey.placeholder = '已设置 API Key（如需更换请重新输入）';
            }
            if (pixabayKey && config.pixabay_api_key_set) {
                pixabayKey.placeholder = '已设置 API Key（如需更换请重新输入）';
            }
            if (config.pandoc_path) {
                pandocPath.value = config.pandoc_path;
            }
            if (config.output_directory) {
                outputDirectory.value = config.output_directory;
            }
            if (config.default_prompt) {
                defaultPrompt.value = config.default_prompt;
            }
            if (config.max_concurrent_tasks) {
                maxConcurrentTasks.value = config.max_concurrent_tasks;
            }

            applyComfyuiSettings(config.comfyui_settings);

            // 加载图片数量配置
            if (comfyuiImageCount && config.comfyui_image_count) {
                comfyuiImageCount.value = config.comfyui_image_count;
            }

            // 加载风格模板下拉选项
            if (comfyuiStyleTemplate && config.comfyui_style_templates) {
                comfyuiStyleTemplate.innerHTML = '';
                config.comfyui_style_templates.forEach(template => {
                    const option = document.createElement('option');
                    option.value = template.id;
                    option.textContent = template.label;
                    comfyuiStyleTemplate.appendChild(option);
                });
                // 设置当前值
                if (config.comfyui_style_template) {
                    comfyuiStyleTemplate.value = config.comfyui_style_template;
                }
                // 初始化显示/隐藏自定义风格块
                toggleCustomStyleBlocks();
            }

            // 加载摘要模型下拉选项（从模型列表动态获取）
            await loadSummaryModels();
            if (config.comfyui_summary_model) {
                comfyuiSummaryModel.value = config.comfyui_summary_model;
            }

            if (comfyuiPositiveStyle) {
                comfyuiPositiveStyle.value = config.comfyui_positive_style || '';
            }
            if (comfyuiNegativeStyle) {
                comfyuiNegativeStyle.value = config.comfyui_negative_style || '';
            }

            // 加载本地图片目录
            if (localImageDirs && config.local_image_directories) {
                loadImageDirectories(config.local_image_directories);
            } else if (localImageDirs) {
                loadImageDirectories([]);
            }

            // 先加载模型列表，然后设置默认模型
            await loadModels();
            if (config.default_model) {
                defaultModel.value = config.default_model;
            }
        }
    } catch (error) {
        console.error('加载配置失败:', error);
    }
}

// 加载模型列表
async function loadModels() {
    try {
        const response = await fetch('/api/models');
        if (response.ok) {
            const data = await response.json();
            defaultModel.innerHTML = '';
            data.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.name;
                option.textContent = model.display_name || model.name;
                defaultModel.appendChild(option);
            });
        } else {
            // 加载失败，提供一个默认选项
            defaultModel.innerHTML = '<option value="gemini-pro">gemini-pro (加载列表失败)</option>';
        }
    } catch (error) {
        // 如果加载失败，保留默认选项
        console.error('加载模型列表失败:', error);
    }
}

// 加载摘要模型列表（复用主模型列表，并添加特殊选项）
async function loadSummaryModels() {
    try {
        const response = await fetch('/api/models');
        if (response.ok) {
            const data = await response.json();
            comfyuiSummaryModel.innerHTML = '';

            // 首先添加特殊选项
            const defaultOption = document.createElement('option');
            defaultOption.value = '__default__';
            defaultOption.textContent = '使用主写作模型';
            comfyuiSummaryModel.appendChild(defaultOption);

            // 然后添加所有可用模型
            data.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.name;
                option.textContent = model.display_name || model.name;
                comfyuiSummaryModel.appendChild(option);
            });
        } else {
            // 加载失败，提供默认选项
            comfyuiSummaryModel.innerHTML = '<option value="__default__">使用主写作模型 (加载列表失败)</option>';
        }
    } catch (error) {
        console.error('加载摘要模型列表失败:', error);
        comfyuiSummaryModel.innerHTML = '<option value="__default__">使用主写作模型 (加载列表失败)</option>';
    }
}

// 切换自定义风格块的显示/隐藏
function toggleCustomStyleBlocks() {
    const customBlocks = document.querySelectorAll('.custom-style-block');
    const isCustom = comfyuiStyleTemplate && comfyuiStyleTemplate.value === 'custom';

    customBlocks.forEach(block => {
        if (isCustom) {
            block.style.display = 'block';
        } else {
            block.style.display = 'none';
        }
    });
}

// 监听风格模板选择变化
if (comfyuiStyleTemplate) {
    comfyuiStyleTemplate.addEventListener('change', toggleCustomStyleBlocks);
}

// 显示状态消息
function showStatus(message, isSuccess) {
    configStatus.textContent = message;
    configStatus.className = 'status-message ' + (isSuccess ? 'success' : 'error');
    configStatus.style.display = 'block';

    setTimeout(() => {
        configStatus.style.display = 'none';
    }, 3000);
}

// 保存配置
saveConfigBtn.addEventListener('click', async () => {
    const newConfig = {
        gemini_base_url: geminiBaseUrl.value || 'https://generativelanguage.googleapis.com',
        pandoc_path: pandocPath.value,
        output_directory: outputDirectory.value || 'output',
        default_model: defaultModel.value,
        default_prompt: defaultPrompt.value,
        max_concurrent_tasks: maxConcurrentTasks.value || 3,
        comfyui_settings: collectComfyuiSettings(),
        comfyui_image_count: parseInt(comfyuiImageCount?.value || 1),
        comfyui_style_template: comfyuiStyleTemplate?.value || 'custom',
        comfyui_positive_style: comfyuiPositiveStyle?.value?.trim() || '',
        comfyui_negative_style: comfyuiNegativeStyle?.value?.trim() || '',
        comfyui_summary_model: comfyuiSummaryModel?.value || '__default__'
    };

    // 只在用户输入了新值时添加到请求中
    if (geminiApiKey.value) {
        newConfig.gemini_api_key = geminiApiKey.value;
    }

    if (unsplashKey.value) {
        newConfig.unsplash_access_key = unsplashKey.value;
    }

    if (pexelsKey && pexelsKey.value) {
        newConfig.pexels_api_key = pexelsKey.value;
    }

    if (pixabayKey && pixabayKey.value) {
        newConfig.pixabay_api_key = pixabayKey.value;
    }

    // 添加本地图片目录配置
    if (localImageDirs) {
        newConfig.local_image_directories = getImageDirectories();
    }

    // 添加图片源优先级配置
    if (imagePriorityList) {
        newConfig.image_source_priority = getImagePriority();
    }

    try {
        saveConfigBtn.disabled = true;
        saveConfigBtn.textContent = '保存中...';

        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(newConfig)
        });

        if (response.ok) {
            showStatus('配置保存成功！', true);
            // 重新加载配置
            await loadConfig();
            // 清空输入框
            geminiApiKey.value = '';
            unsplashKey.value = '';
            if (pexelsKey) pexelsKey.value = '';
            if (pixabayKey) pixabayKey.value = '';
            // 重新加载模型列表
            await loadModels();
        } else {
            showStatus('配置保存失败！', false);
        }
    } catch (error) {
        console.error('保存配置失败:', error);
        showStatus('保存配置时发生错误！', false);
    } finally {
        saveConfigBtn.disabled = false;
        saveConfigBtn.textContent = '保存配置';
    }
});

// 测试 Unsplash API
testUnsplashBtn.addEventListener('click', async () => {
    const apiKey = unsplashKey.value;

    if (!apiKey) {
        unsplashTestResult.textContent = '请先输入 Unsplash Access Key';
        unsplashTestResult.className = 'test-result error';
        unsplashTestResult.style.display = 'block';
        return;
    }

    testUnsplashBtn.disabled = true;
    testUnsplashBtn.textContent = '测试中...';
    unsplashTestResult.textContent = '正在测试 API...';
    unsplashTestResult.className = 'test-result info';
    unsplashTestResult.style.display = 'block';

    try {
        const response = await fetch('/api/test-unsplash', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ access_key: apiKey })
        });

        const result = await response.json();

        if (result.success) {
            unsplashTestResult.textContent = `✓ 测试成功！找到图片：${result.image_url}`;
            unsplashTestResult.className = 'test-result success';
        } else {
            unsplashTestResult.textContent = `✗ 测试失败：${result.error}`;
            unsplashTestResult.className = 'test-result error';
        }
    } catch (error) {
        unsplashTestResult.textContent = `✗ 测试失败：${error.message}`;
        unsplashTestResult.className = 'test-result error';
    } finally {
        testUnsplashBtn.disabled = false;
        testUnsplashBtn.textContent = '测试 Unsplash API';
    }
});

// 重置配置
resetConfigBtn.addEventListener('click', () => {
    if (confirm('确定要重置为默认配置吗？')) {
        geminiApiKey.value = '';
        geminiBaseUrl.value = 'https://generativelanguage.googleapis.com';
        unsplashKey.value = '';
        pexelsKey.value = '';
        pixabayKey.value = '';
        pandocPath.value = '';
        outputDirectory.value = 'output';
        defaultModel.value = 'gemini-pro';
        defaultPrompt.value = '';
        maxConcurrentTasks.value = 3;
        applyComfyuiSettings(comfyuiDefaults);
        if (comfyuiImageCount) comfyuiImageCount.value = 1;
        if (comfyuiStyleTemplate) comfyuiStyleTemplate.value = 'custom';
        if (comfyuiPositiveStyle) comfyuiPositiveStyle.value = '';
        if (comfyuiNegativeStyle) comfyuiNegativeStyle.value = '';
        if (comfyuiSummaryModel) comfyuiSummaryModel.value = '__default__';
        toggleCustomStyleBlocks(); // 更新自定义块显示状态
        if (typeof reorderPriorityList === 'function' && imagePriorityList) {
            reorderPriorityList(['comfyui', 'user_uploaded', 'pexels', 'unsplash', 'pixabay', 'local']);
        }
        if (comfyuiTestResult) {
            comfyuiTestResult.style.display = 'none';
            comfyuiTestResult.textContent = '';
        }
        showStatus('已重置为默认值（尚未保存）', true);
    }
});

// ============ 新增图片API测试功能 ============

// 测试 Pexels API
if (testPexelsBtn) {
    testPexelsBtn.addEventListener('click', async () => {
        const apiKey = pexelsKey.value;

        if (!apiKey) {
            pexelsTestResult.textContent = '请先输入 Pexels API Key';
            pexelsTestResult.className = 'test-result error';
            pexelsTestResult.style.display = 'block';
            return;
        }

        testPexelsBtn.disabled = true;
        testPexelsBtn.textContent = '测试中...';
        pexelsTestResult.textContent = '正在测试 API...';
        pexelsTestResult.className = 'test-result info';
        pexelsTestResult.style.display = 'block';

        try {
            const response = await fetch('/api/test-pexels', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: apiKey })
            });

            const result = await response.json();

            if (result.success) {
                pexelsTestResult.textContent = `✓ 测试成功！找到图片：${result.image_url}`;
                pexelsTestResult.className = 'test-result success';
            } else {
                pexelsTestResult.textContent = `✗ 测试失败：${result.error}`;
                pexelsTestResult.className = 'test-result error';
            }
        } catch (error) {
            pexelsTestResult.textContent = `✗ 测试失败：${error.message}`;
            pexelsTestResult.className = 'test-result error';
        } finally {
            testPexelsBtn.disabled = false;
            testPexelsBtn.textContent = '测试 Pexels API';
        }
    });
}

// 测试 Pixabay API
if (testPixabayBtn) {
    testPixabayBtn.addEventListener('click', async () => {
        const apiKey = pixabayKey.value;

        if (!apiKey) {
            pixabayTestResult.textContent = '请先输入 Pixabay API Key';
            pixabayTestResult.className = 'test-result error';
            pixabayTestResult.style.display = 'block';
            return;
        }

        testPixabayBtn.disabled = true;
        testPixabayBtn.textContent = '测试中...';
        pixabayTestResult.textContent = '正在测试 API...';
        pixabayTestResult.className = 'test-result info';
        pixabayTestResult.style.display = 'block';

        try {
            const response = await fetch('/api/test-pixabay', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: apiKey })
            });

            const result = await response.json();

            if (result.success) {
                pixabayTestResult.textContent = `✓ 测试成功！找到图片：${result.image_url}`;
                pixabayTestResult.className = 'test-result success';
            } else {
                pixabayTestResult.textContent = `✗ 测试失败：${result.error}`;
                pixabayTestResult.className = 'test-result error';
            }
        } catch (error) {
            pixabayTestResult.textContent = `✗ 测试失败：${error.message}`;
            pixabayTestResult.className = 'test-result error';
        } finally {
            testPixabayBtn.disabled = false;
            testPixabayBtn.textContent = '测试 Pixabay API';
        }
    });
}

// 测试主模型
if (testDefaultModelBtn) {
    testDefaultModelBtn.addEventListener('click', async () => {
        const modelName = defaultModel.value;
        const apiKey = geminiApiKey.value || ''; // 如果输入了新的就用新的，否则后端会用已保存的
        const baseUrl = geminiBaseUrl.value || 'https://generativelanguage.googleapis.com';

        if (!modelName) {
            defaultModelTestResult.textContent = '请先选择模型';
            defaultModelTestResult.className = 'test-result error';
            defaultModelTestResult.style.display = 'block';
            return;
        }

        testDefaultModelBtn.disabled = true;
        testDefaultModelBtn.textContent = '测试中...';
        defaultModelTestResult.textContent = '正在测试模型...';
        defaultModelTestResult.className = 'test-result info';
        defaultModelTestResult.style.display = 'block';

        try {
            const response = await fetch('/api/test-model', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model_name: modelName,
                    api_key: apiKey,
                    base_url: baseUrl
                })
            });

            const result = await response.json();

            if (result.success) {
                defaultModelTestResult.textContent = `✓ ${result.message}\n回复: ${result.reply}`;
                defaultModelTestResult.className = 'test-result success';
            } else {
                defaultModelTestResult.textContent = `✗ ${result.error}`;
                defaultModelTestResult.className = 'test-result error';
            }
        } catch (error) {
            defaultModelTestResult.textContent = `✗ 测试失败：${error.message}`;
            defaultModelTestResult.className = 'test-result error';
        } finally {
            testDefaultModelBtn.disabled = false;
            testDefaultModelBtn.textContent = '测试主模型';
        }
    });
}

// 测试摘要模型
if (testSummaryModelBtn) {
    testSummaryModelBtn.addEventListener('click', async () => {
        const modelName = comfyuiSummaryModel.value;

        if (!modelName || modelName === '__default__') {
            summaryModelTestResult.textContent = '请先选择具体的摘要模型（不能选择"使用主写作模型"）';
            summaryModelTestResult.className = 'test-result error';
            summaryModelTestResult.style.display = 'block';
            return;
        }

        const apiKey = geminiApiKey.value || '';
        const baseUrl = geminiBaseUrl.value || 'https://generativelanguage.googleapis.com';

        testSummaryModelBtn.disabled = true;
        testSummaryModelBtn.textContent = '测试中...';
        summaryModelTestResult.textContent = '正在测试模型...';
        summaryModelTestResult.className = 'test-result info';
        summaryModelTestResult.style.display = 'block';

        try {
            const response = await fetch('/api/test-model', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model_name: modelName,
                    api_key: apiKey,
                    base_url: baseUrl
                })
            });

            const result = await response.json();

            if (result.success) {
                summaryModelTestResult.textContent = `✓ ${result.message}\n回复: ${result.reply}`;
                summaryModelTestResult.className = 'test-result success';
            } else {
                summaryModelTestResult.textContent = `✗ ${result.error}`;
                summaryModelTestResult.className = 'test-result error';
            }
        } catch (error) {
            summaryModelTestResult.textContent = `✗ 测试失败：${error.message}`;
            summaryModelTestResult.className = 'test-result error';
        } finally {
            testSummaryModelBtn.disabled = false;
            testSummaryModelBtn.textContent = '测试摘要模型';
        }
    });
}

// 测试 ComfyUI Workflow
if (testComfyuiBtn) {
    testComfyuiBtn.addEventListener('click', async () => {
        const settings = collectComfyuiSettings();

        if (!settings.workflow_path) {
            comfyuiTestResult.textContent = '请先配置 Workflow JSON 路径';
            comfyuiTestResult.className = 'test-result error';
            comfyuiTestResult.style.display = 'block';
            return;
        }

        testComfyuiBtn.disabled = true;
        testComfyuiBtn.textContent = '测试中...';
        if (comfyuiTestResult) {
            comfyuiTestResult.textContent = '正在调用 ComfyUI...';
            comfyuiTestResult.className = 'test-result info';
            comfyuiTestResult.style.display = 'block';
        }

        try {
            const response = await fetch('/api/test-comfyui', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    comfyui_settings: settings,
                    comfyui_positive_style: comfyuiPositiveStyle?.value?.trim() || '',
                    comfyui_negative_style: comfyuiNegativeStyle?.value?.trim() || ''
                })
            });

            const result = await response.json();
            if (result.success) {
                const path = result.image_path || '已生成图片';
                comfyuiTestResult.textContent = `✓ 测试成功！输出文件：${path}`;
                comfyuiTestResult.className = 'test-result success';
            } else {
                comfyuiTestResult.textContent = `✗ 测试失败：${result.error}`;
                comfyuiTestResult.className = 'test-result error';
            }
        } catch (error) {
            comfyuiTestResult.textContent = `✗ 测试失败：${error.message}`;
            comfyuiTestResult.className = 'test-result error';
        } finally {
            testComfyuiBtn.disabled = false;
            testComfyuiBtn.textContent = '测试 ComfyUI 工作流';
        }
    });
}

// ============ 本地图库目录管理 ============

let imageDirCount = 0;

// 添加图片目录
if (addImageDirBtn) {
    addImageDirBtn.addEventListener('click', () => {
        addImageDirectory();
    });
}

function addImageDirectory(path = '', tags = []) {
    const dirItem = document.createElement('div');
    dirItem.className = 'image-dir-item';
    dirItem.dataset.index = imageDirCount++;

    dirItem.innerHTML = `
        <div class="form-group-inline">
            <div>
                <label>目录路径:</label>
                <input type="text" class="dir-path" value="${path}" placeholder="例如: images/nature">
            </div>
            <div>
                <label>标签（逗号分隔）:</label>
                <input type="text" class="dir-tags" value="${tags.join(', ')}" placeholder="例如: nature, landscape">
            </div>
            <button type="button" class="btn btn-secondary btn-small remove-dir-btn">删除</button>
        </div>
    `;

    const removeBtn = dirItem.querySelector('.remove-dir-btn');
    removeBtn.addEventListener('click', () => {
        dirItem.remove();
    });

    localImageDirs.appendChild(dirItem);
}

function loadImageDirectories(directories) {
    localImageDirs.innerHTML = '';
    imageDirCount = 0;

    if (directories && directories.length > 0) {
        directories.forEach(dir => {
            addImageDirectory(dir.path, dir.tags || []);
        });
    } else {
        // 默认添加一个
        addImageDirectory('pic', ['default']);
    }
}

function getImageDirectories() {
    const dirItems = localImageDirs.querySelectorAll('.image-dir-item');
    const directories = [];

    dirItems.forEach(item => {
        const path = item.querySelector('.dir-path').value.trim();
        const tagsStr = item.querySelector('.dir-tags').value.trim();
        const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()).filter(t => t) : [];

        if (path) {
            directories.push({ path, tags });
        }
    });

    return directories;
}

// ============ 图片源优先级拖拽排序 ============

const imagePriorityList = document.getElementById('imagePriorityList');

if (imagePriorityList) {
    // 初始化拖拽功能
    initializeDragAndDrop();

    // 加载优先级配置
    loadImagePriority();
}

function initializeDragAndDrop() {
    const items = imagePriorityList.querySelectorAll('li');

    items.forEach(item => {
        item.draggable = true;

        item.addEventListener('dragstart', handleDragStart);
        item.addEventListener('dragover', handleDragOver);
        item.addEventListener('drop', handleDrop);
        item.addEventListener('dragend', handleDragEnd);
        item.addEventListener('dragenter', handleDragEnter);
        item.addEventListener('dragleave', handleDragLeave);
    });
}

let draggedItem = null;

function handleDragStart(e) {
    draggedItem = this;
    this.style.opacity = '0.4';
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', this.innerHTML);
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    return false;
}

function handleDragEnter(e) {
    if (this !== draggedItem) {
        this.style.borderTop = '3px solid #007bff';
    }
}

function handleDragLeave(e) {
    this.style.borderTop = '';
}

function handleDrop(e) {
    e.stopPropagation();
    e.preventDefault();

    if (draggedItem !== this) {
        // 获取所有项
        const allItems = Array.from(imagePriorityList.children);
        const draggedIndex = allItems.indexOf(draggedItem);
        const targetIndex = allItems.indexOf(this);

        // 重新排序
        if (draggedIndex < targetIndex) {
            this.parentNode.insertBefore(draggedItem, this.nextSibling);
        } else {
            this.parentNode.insertBefore(draggedItem, this);
        }
    }

    this.style.borderTop = '';
    return false;
}

function handleDragEnd(e) {
    this.style.opacity = '1';

    // 移除所有项的边框
    const items = imagePriorityList.querySelectorAll('li');
    items.forEach(item => {
        item.style.borderTop = '';
    });
}

function loadImagePriority() {
    // 从配置加载并重新排序列表
    fetch('/api/config')
        .then(response => response.json())
        .then(config => {
            if (config.image_source_priority && config.image_source_priority.length > 0) {
                reorderPriorityList(config.image_source_priority);
            }
        })
        .catch(error => {
            console.error('加载图片优先级失败:', error);
        });
}

function reorderPriorityList(priority) {
    const items = Array.from(imagePriorityList.children);
    const orderedItems = [];

    // 按照优先级顺序重新排列
    priority.forEach(source => {
        const item = items.find(i => i.dataset.source === source);
        if (item) {
            orderedItems.push(item);
        }
    });

    // 添加配置中没有的项（如果有的话）
    items.forEach(item => {
        if (!orderedItems.includes(item)) {
            orderedItems.push(item);
        }
    });

    // 重新插入到列表中
    imagePriorityList.innerHTML = '';
    orderedItems.forEach(item => {
        imagePriorityList.appendChild(item);
    });

    // 重新初始化拖拽功能
    initializeDragAndDrop();
}

function getImagePriority() {
    const items = imagePriorityList.querySelectorAll('li');
    const priority = [];

    items.forEach(item => {
        const source = item.dataset.source;
        if (source) {
            priority.push(source);
        }
    });

    return priority;
}
