// 全局变量
let config = {};

// DOM 元素
const toggleConfigBtn = document.getElementById('toggleConfig');
const configPanel = document.getElementById('configPanel');
const saveConfigBtn = document.getElementById('saveConfig');
const refreshModelsBtn = document.getElementById('refreshModels');
const generateBtn = document.getElementById('generateBtn');
const clearBtn = document.getElementById('clearBtn');
const topicInput = document.getElementById('topicInput');
const progressArea = document.getElementById('progressArea');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const resultsArea = document.getElementById('resultsArea');
const resultsList = document.getElementById('resultsList');

// 页面加载时获取配置
document.addEventListener('DOMContentLoaded', () => {
    loadConfig();
});

// 切换配置面板显示
toggleConfigBtn.addEventListener('click', () => {
    if (configPanel.style.display === 'none') {
        configPanel.style.display = 'block';
    } else {
        configPanel.style.display = 'none';
    }
});

// 加载配置
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        if (response.ok) {
            config = await response.json();
            updateConfigUI();
        }
    } catch (error) {
        console.error('加载配置失败:', error);
    }
}

// 更新配置界面
function updateConfigUI() {
    if (config.gemini_api_key_set) {
        document.getElementById('geminiApiKey').placeholder = '已设置 API Key（如需更换请重新输入）';
    }
    if (config.gemini_base_url) {
        document.getElementById('geminiBaseUrl').value = config.gemini_base_url;
    }
    if (config.unsplash_access_key_set) {
        document.getElementById('unsplashKey').placeholder = '已设置 Access Key（如需更换请重新输入）';
    }
    if (config.default_model) {
        document.getElementById('modelSelect').value = config.default_model;
    }
}

// 保存配置
saveConfigBtn.addEventListener('click', async () => {
    const geminiApiKey = document.getElementById('geminiApiKey').value;
    const geminiBaseUrl = document.getElementById('geminiBaseUrl').value;
    const unsplashKey = document.getElementById('unsplashKey').value;
    const defaultModel = document.getElementById('modelSelect').value;

    const newConfig = {
        gemini_base_url: geminiBaseUrl || 'https://generativelanguage.googleapis.com',
        default_model: defaultModel
    };

    // 只在用户输入了新值时添加到请求中
    if (geminiApiKey) {
        newConfig.gemini_api_key = geminiApiKey;
    }

    if (unsplashKey) {
        newConfig.unsplash_access_key = unsplashKey;
    }

    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(newConfig)
        });

        if (response.ok) {
            alert('配置保存成功！');
            // 重新加载配置
            await loadConfig();
            // 清空输入框
            document.getElementById('geminiApiKey').value = '';
            document.getElementById('unsplashKey').value = '';
        } else {
            alert('配置保存失败！');
        }
    } catch (error) {
        console.error('保存配置失败:', error);
        alert('保存配置时发生错误！');
    }
});

// 刷新模型列表
refreshModelsBtn.addEventListener('click', async () => {
    try {
        refreshModelsBtn.textContent = '加载中...';
        refreshModelsBtn.disabled = true;

        const response = await fetch('/api/models');
        if (response.ok) {
            const data = await response.json();
            const modelSelect = document.getElementById('modelSelect');
            modelSelect.innerHTML = '';

            data.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.name;
                option.textContent = model.display_name || model.name;
                modelSelect.appendChild(option);
            });

            alert('模型列表刷新成功！');
        } else {
            const error = await response.json();
            alert('获取模型列表失败: ' + error.error);
        }
    } catch (error) {
        console.error('刷新模型列表失败:', error);
        alert('刷新模型列表时发生错误！');
    } finally {
        refreshModelsBtn.textContent = '刷新模型列表';
        refreshModelsBtn.disabled = false;
    }
});

// 清空输入
clearBtn.addEventListener('click', () => {
    topicInput.value = '';
    resultsArea.style.display = 'none';
    progressArea.style.display = 'none';
});

// 生成文章
generateBtn.addEventListener('click', async () => {
    const topicsText = topicInput.value.trim();

    if (!topicsText) {
        alert('请输入至少一个文章标题或主题！');
        return;
    }

    // 分割主题（按行）
    const topics = topicsText.split('\n').filter(t => t.trim()).map(t => t.trim());

    if (topics.length === 0) {
        alert('请输入有效的文章标题或主题！');
        return;
    }

    // 获取选中的模型
    const selectedModel = document.getElementById('modelSelect').value;

    // 显示进度
    progressArea.style.display = 'block';
    resultsArea.style.display = 'none';
    progressFill.style.width = '0%';
    progressText.textContent = '正在生成文章...';

    // 禁用生成按钮
    generateBtn.disabled = true;
    generateBtn.textContent = '生成中...';

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                topics: topics,
                model: selectedModel
            })
        });

        if (response.ok) {
            const data = await response.json();
            progressFill.style.width = '100%';
            progressText.textContent = '生成完成！';

            // 显示结果
            displayResults(data.results);
        } else {
            const error = await response.json();
            alert('生成失败: ' + error.error);
            progressArea.style.display = 'none';
        }
    } catch (error) {
        console.error('生成文章失败:', error);
        alert('生成文章时发生错误！');
        progressArea.style.display = 'none';
    } finally {
        // 恢复生成按钮
        generateBtn.disabled = false;
        generateBtn.textContent = '开始生成';
    }
});

// 显示结果
function displayResults(results) {
    resultsArea.style.display = 'block';
    resultsList.innerHTML = '';

    results.forEach(result => {
        const resultItem = document.createElement('div');
        resultItem.className = 'result-item ' + (result.success ? 'success' : 'error');

        if (result.success) {
            resultItem.innerHTML = `
                <div class="result-title">✓ ${result.topic}</div>
                <div class="result-info">图片关键词: ${result.image_keyword}</div>
                <div class="result-info">文件名: ${result.filename}</div>
                <a href="/api/download/${result.filename}" class="download-btn" download>下载 Word 文档</a>
            `;
        } else {
            resultItem.innerHTML = `
                <div class="result-title">✗ ${result.topic}</div>
                <div class="result-info" style="color: #d32f2f;">错误: ${result.error}</div>
            `;
        }

        resultsList.appendChild(resultItem);
    });

    // 滚动到结果区域
    resultsArea.scrollIntoView({ behavior: 'smooth' });
}

// 模拟进度更新（实际应用中可以通过 WebSocket 或轮询实现实时进度）
function updateProgress(percent) {
    progressFill.style.width = percent + '%';
}
