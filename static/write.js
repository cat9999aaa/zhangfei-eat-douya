// DOM 元素
const topicsContainer = document.getElementById('topicsContainer');
const addTopicBtn = document.getElementById('addTopicBtn');
const enableImage = document.getElementById('enableImage');
const generateBtn = document.getElementById('generateBtn');
const clearBtn = document.getElementById('clearBtn');
const progressArea = document.getElementById('progressArea');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const resultsArea = document.getElementById('resultsArea');
const resultsList = document.getElementById('resultsList');

let topicCount = 0;
const MAX_TOPICS = 50;

// 存储每个主题的图片设置
const topicImages = new Map(); // key: topicIndex, value: {type, data, preview}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', async () => {
    // 恢复保存的状态
    restorePageState();

    // 恢复正在进行的任务
    restoreTaskProgress();

    // 检查 Pandoc 配置并显示提示
    try {
        const checkResponse = await fetch('/api/check-pandoc');
        const checkData = await checkResponse.json();

        if (!checkData.pandoc_configured) {
            // 在页面顶部显示警告信息
            const warningDiv = document.createElement('div');
            warningDiv.style.cssText = 'background: #fff3cd; border: 2px solid #ffc107; color: #856404; padding: 15px; margin-bottom: 20px; border-radius: 8px; text-align: center; font-weight: 600;';
            warningDiv.innerHTML = '⚠️ 请先在<a href="/config" style="color: #007bff; text-decoration: underline;">配置页面</a>设置 Pandoc 路径，否则无法生成文章！';
            document.querySelector('.main-content').insertBefore(warningDiv, document.querySelector('.main-content').firstChild);
        }
    } catch (error) {
        console.error('检查 Pandoc 配置失败:', error);
    }
});

// 保存页面状态
function savePageState() {
    const topics = getAllTopics();
    const state = {
        topics: topics,
        enableImage: enableImage.checked,
        timestamp: Date.now()
    };
    localStorage.setItem('writePageState', JSON.stringify(state));
}

// 恢复页面状态
function restorePageState() {
    const savedState = localStorage.getItem('writePageState');

    if (savedState) {
        try {
            const state = JSON.parse(savedState);

            // 如果状态是24小时内保存的，就恢复
            if (Date.now() - state.timestamp < 24 * 60 * 60 * 1000) {
                // 恢复主题
                if (state.topics && state.topics.length > 0) {
                    state.topics.forEach(topic => {
                        addTopicInput();
                        const inputs = document.querySelectorAll('.topic-input');
                        inputs[inputs.length - 1].value = topic;
                    });
                } else {
                    addTopicInput();
                }

                // 恢复图片选项
                if (state.enableImage !== undefined) {
                    enableImage.checked = state.enableImage;
                }
            } else {
                // 状态过期，添加第一个输入框
                addTopicInput();
            }
        } catch (e) {
            console.error('恢复页面状态失败:', e);
            addTopicInput();
        }
    } else {
        // 没有保存的状态，添加第一个输入框
        addTopicInput();
    }
}

// 清除保存的状态
function clearPageState() {
    localStorage.removeItem('writePageState');
}

// 添加主题输入框
function addTopicInput() {
    if (topicCount >= MAX_TOPICS) {
        alert(`最多只能添加 ${MAX_TOPICS} 个标题`);
        return;
    }

    const currentIndex = topicCount; // 保存当前索引

    const wrapper = document.createElement('div');
    wrapper.className = 'topic-input-wrapper';
    wrapper.dataset.index = currentIndex;

    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = `标题 ${currentIndex + 1}`;
    input.className = 'topic-input';

    // 监听输入变化，自动保存状态
    input.addEventListener('input', () => {
        savePageState();
    });

    // 添加图片设置按钮
    const imageBtn = document.createElement('button');
    imageBtn.textContent = '🖼️ 图片设置';
    imageBtn.className = 'image-set-btn';
    imageBtn.type = 'button';
    // 使用闭包捕获正确的索引
    imageBtn.onclick = function() {
        openImageModal(parseInt(this.parentElement.dataset.index));
    };

    const removeBtn = document.createElement('button');
    removeBtn.textContent = '删除';
    removeBtn.className = 'remove-btn';
    removeBtn.onclick = () => {
        const index = parseInt(wrapper.dataset.index);
        topicImages.delete(index);
        wrapper.remove();
        topicCount--;
        updateAddButtonState();
        savePageState();
    };

    wrapper.appendChild(input);
    wrapper.appendChild(imageBtn);
    // 如果不是第一个输入框，显示删除按钮
    if (currentIndex > 0) {
        wrapper.appendChild(removeBtn);
    }

    topicsContainer.appendChild(wrapper);
    topicCount++;
    updateAddButtonState();
}

// 更新添加按钮状态
function updateAddButtonState() {
    addTopicBtn.disabled = topicCount >= MAX_TOPICS;
    if (topicCount >= MAX_TOPICS) {
        addTopicBtn.textContent = `已达到最大数量 (${MAX_TOPICS})`;
    } else {
        addTopicBtn.textContent = '+ 添加标题';
    }
}

// 获取所有主题
function getAllTopics() {
    const inputs = document.querySelectorAll('.topic-input');
    const topics = [];
    inputs.forEach(input => {
        if (input.value.trim()) {
            topics.push(input.value.trim());
        }
    });
    return topics;
}

// 添加标题按钮事件
addTopicBtn.addEventListener('click', addTopicInput);

// 清空输入
clearBtn.addEventListener('click', () => {
    topicsContainer.innerHTML = '';
    topicCount = 0;
    addTopicInput();
    resultsArea.style.display = 'none';
    progressArea.style.display = 'none';
});

let currentTaskId = null;
let statusInterval = null;

// 保存任务进度到localStorage
function saveTaskProgress() {
    if (currentTaskId) {
        const taskData = {
            taskId: currentTaskId,
            timestamp: Date.now()
        };
        localStorage.setItem('currentTask', JSON.stringify(taskData));
    }
}

// 恢复任务进度
async function restoreTaskProgress() {
    const savedTask = localStorage.getItem('currentTask');

    if (savedTask) {
        try {
            const taskData = JSON.parse(savedTask);
            const taskId = taskData.taskId;

            // 检查任务是否仍然存在
            const response = await fetch(`/api/generate/status/${taskId}`);
            if (response.ok) {
                const task = await response.json();

                // 如果任务未完成，恢复轮询
                if (task.status === 'running') {
                    currentTaskId = taskId;
                    progressArea.style.display = 'block';
                    resultsArea.style.display = 'block';
                    generateBtn.disabled = true;
                    generateBtn.textContent = '生成中...';

                    startPolling(taskId);
                    updateUI(task);
                } else if (task.status === 'completed') {
                    // 任务已完成，显示结果
                    progressArea.style.display = 'block';
                    resultsArea.style.display = 'block';
                    updateUI(task);
                    progressText.textContent = '全部任务已完成！';

                    // 清除保存的任务
                    localStorage.removeItem('currentTask');
                }
            } else {
                // 任务不存在，清除保存的数据
                localStorage.removeItem('currentTask');
            }
        } catch (error) {
            console.error('恢复任务进度失败:', error);
            localStorage.removeItem('currentTask');
        }
    }
}

// 清除任务进度
function clearTaskProgress() {
    localStorage.removeItem('currentTask');
}

// 生成文章
generateBtn.addEventListener('click', async () => {
    const inputs = document.querySelectorAll('.topic-input');
    const topics = [];
    const topicImageMap = {};

    // 收集主题和对应的图片
    inputs.forEach((input, index) => {
        const topic = input.value.trim();
        if (topic) {
            topics.push(topic);

            // 如果这个主题有设置图片
            if (topicImages.has(index)) {
                const imageData = topicImages.get(index);
                if (imageData.type === 'url') {
                    topicImageMap[topic] = {
                        type: 'url',
                        url: imageData.url
                    };
                } else if (imageData.uploadedPath) {
                    topicImageMap[topic] = {
                        type: 'uploaded',
                        path: imageData.uploadedPath
                    };
                }
            }
        }
    });

    if (topics.length === 0) {
        alert('请至少输入一个文章标题或主题！');
        return;
    }

    // 检查 Pandoc 配置
    try {
        const checkResponse = await fetch('/api/check-pandoc');
        const checkData = await checkResponse.json();
        if (!checkData.pandoc_configured) {
            alert('请先在配置页面设置 Pandoc 可执行文件路径！');
            return;
        }
    } catch (error) {
        alert('检查配置时发生错误，请稍后重试。');
        return;
    }

    // 重置UI
    progressArea.style.display = 'block';
    resultsArea.style.display = 'block'; // 保持结果区域可见
    resultsList.innerHTML = '';
    progressFill.style.width = '0%';
    progressText.textContent = '正在启动任务...';
    generateBtn.disabled = true;
    generateBtn.textContent = '生成中...';

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topics: topics,
                topic_images: topicImageMap
            })
        });

        if (response.ok) {
            const data = await response.json();
            currentTaskId = data.task_id;
            saveTaskProgress(); // 保存任务ID
            startPolling(currentTaskId);
        } else {
            const error = await response.json();
            alert('启动生成任务失败: ' + error.error);
            resetUI();
        }
    } catch (error) {
        alert('启动生成任务时发生错误！');
        resetUI();
    }
});


function startPolling(taskId) {
    // 立即执行一次，避免延迟
    pollStatus(taskId);

    // 设置定时轮询
    statusInterval = setInterval(() => {
        pollStatus(taskId);
    }, 2000); // 每2秒轮询一次
}

async function pollStatus(taskId) {
    try {
        const response = await fetch(`/api/generate/status/${taskId}`);
        if (response.ok) {
            const task = await response.json();
            updateUI(task);

            if (task.status === 'completed') {
                clearInterval(statusInterval);
                statusInterval = null;
                progressText.textContent = '全部任务已完成！';
                generateBtn.disabled = false;
                generateBtn.textContent = '开始生成';
                clearTaskProgress(); // 清除保存的任务进度
            }
        } else if (response.status === 404) {
            // 任务可能已因服务器重启而丢失
            clearInterval(statusInterval);
            statusInterval = null;
            clearTaskProgress();
            alert('任务状态查询失败，任务可能已丢失。');
            resetUI();
        }
    } catch (error) {
        console.error('轮询状态失败:', error);
        // 可以在这里添加一些网络错误处理逻辑
    }
}

function updateUI(task) {
    // 调试信息
    console.log('更新UI - 任务状态:', {
        status: task.status,
        total: task.total,
        results: task.results.length,
        errors: task.errors.length,
        progress: task.progress
    });

    // 更新进度条
    progressFill.style.width = `${task.progress}%`;
    const completedCount = task.results.length + task.errors.length;
    progressText.textContent = `生成中... (${completedCount}/${task.total}) - ${Math.round(task.progress)}%`;

    // 清空并重新渲染结果列表
    resultsList.innerHTML = '';

    // 显示成功结果
    console.log('渲染成功结果:', task.results);
    task.results.forEach(result => {
        const resultItem = document.createElement('div');
        resultItem.className = 'result-item success';
        resultItem.innerHTML = `
            <div class="result-title">✓ ${result.article_title}</div>
            <a href="/api/download/${result.filename}" class="download-btn" download>下载 Word 文档</a>
        `;
        resultsList.appendChild(resultItem);
    });

    // 显示失败结果
    task.errors.forEach(error => {
        const resultItem = document.createElement('div');
        resultItem.className = 'result-item error';
        resultItem.innerHTML = `
            <div class="result-title">✗ ${error.topic}</div>
            <div class="result-info">错误: ${error.error}</div>
            <div class="result-actions">
                <button class="btn btn-secondary btn-small retry-btn" data-topic="${error.topic}">重试</button>
                <button class="btn btn-secondary btn-small discard-btn">放弃</button>
            </div>
        `;
        resultsList.appendChild(resultItem);
    });

    resultsArea.scrollIntoView({ behavior: 'smooth', block: 'end' });
}


function resetUI() {
    progressArea.style.display = 'none';
    generateBtn.disabled = false;
    generateBtn.textContent = '开始生成';
    if (statusInterval) {
        clearInterval(statusInterval);
        statusInterval = null;
    }
}

// 事件委托：处理重试和放弃按钮的点击
resultsList.addEventListener('click', async (event) => {
    const target = event.target;

    // 处理重试按钮
    if (target.classList.contains('retry-btn')) {
        const topic = target.dataset.topic;
        if (topic && currentTaskId) {
            target.disabled = true;
            target.textContent = '重试中...';
            try {
                const response = await fetch('/api/generate/retry', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        task_id: currentTaskId,
                        topics: [topic]
                    })
                });
                if (response.ok) {
                    // 立即更新UI，表明任务正在重新启动
                    generateBtn.disabled = true;
                    generateBtn.textContent = '生成中...';
                    progressText.textContent = '任务已重新提交，正在更新状态...';

                    // 停止任何现有的轮询并重新启动，以获取最新状态
                    if (statusInterval) {
                        clearInterval(statusInterval);
                    }
                    startPolling(currentTaskId);

                    // 让新的轮询来更新UI，而不是手动移除元素
                } else {
                    alert('重试请求失败！');
                    target.disabled = false;
                    target.textContent = '重试';
                }
            } catch (error) {
                alert('重试时发生错误！');
                target.disabled = false;
                target.textContent = '重试';
            }
        }
    }

    // 处理放弃按钮
    if (target.classList.contains('discard-btn')) {
        // 直接从UI上移除该项
        target.closest('.result-item').remove();
    }
});

// ============ 图片设置模态框功能 ============

let currentTopicIndex = null;
let currentImageData = null;

// 模态框元素
const imageModal = document.getElementById('imageModal');
const modalTopicName = document.getElementById('modalTopicName');
const modalClose = document.querySelector('.modal-close');
const saveImageBtn = document.getElementById('saveImageBtn');
const clearImageBtn = document.getElementById('clearImageBtn');
const cancelImageBtn = document.getElementById('cancelImageBtn');
const modalStatus = document.getElementById('modalStatus');

// Tab切换
const tabBtns = document.querySelectorAll('.tab-btn');
const uploadTab = document.getElementById('uploadTab');
const clipboardTab = document.getElementById('clipboardTab');
const urlTab = document.getElementById('urlTab');

// 上传相关
const selectFileBtn = document.getElementById('selectFileBtn');
const imageFileInput = document.getElementById('imageFileInput');
const uploadPreview = document.getElementById('uploadPreview');
const uploadPreviewImg = document.getElementById('uploadPreviewImg');
const uploadFileName = document.getElementById('uploadFileName');

// 剪贴板相关
const pasteZone = document.getElementById('pasteZone');
const clipboardPreview = document.getElementById('clipboardPreview');
const clipboardPreviewImg = document.getElementById('clipboardPreviewImg');

// URL相关
const imageUrlInput = document.getElementById('imageUrlInput');
const loadUrlBtn = document.getElementById('loadUrlBtn');
const urlPreview = document.getElementById('urlPreview');
const urlPreviewImg = document.getElementById('urlPreviewImg');
const urlStatus = document.getElementById('urlStatus');

// 打开模态框
function openImageModal(topicIndex) {
    const wrapper = document.querySelector(`.topic-input-wrapper[data-index="${topicIndex}"]`);
    if (!wrapper) return;

    const input = wrapper.querySelector('.topic-input');
    const topicText = input.value.trim() || `标题 ${topicIndex + 1}`;

    currentTopicIndex = topicIndex;
    modalTopicName.textContent = topicText;

    // 重置模态框
    resetModal();

    // 如果已有图片设置，显示预览
    if (topicImages.has(topicIndex)) {
        const imageData = topicImages.get(topicIndex);
        loadExistingImage(imageData);
    }

    imageModal.style.display = 'flex';
}

// 关闭模态框
function closeImageModal() {
    imageModal.style.display = 'none';
    currentTopicIndex = null;
    currentImageData = null;
}

// 重置模态框
function resetModal() {
    // 切换到第一个tab
    switchTab('upload');

    // 清空所有预览
    uploadPreview.style.display = 'none';
    uploadPreviewImg.src = '';
    uploadFileName.textContent = '';
    imageFileInput.value = '';

    clipboardPreview.style.display = 'none';
    clipboardPreviewImg.src = '';

    urlPreview.style.display = 'none';
    urlPreviewImg.src = '';
    imageUrlInput.value = '';
    urlStatus.textContent = '';

    modalStatus.style.display = 'none';
    currentImageData = null;
}

// 加载已存在的图片
function loadExistingImage(imageData) {
    switch (imageData.type) {
        case 'upload':
        case 'clipboard':
            switchTab('upload');
            uploadPreview.style.display = 'block';
            uploadPreviewImg.src = imageData.preview;
            uploadFileName.textContent = imageData.filename || '已设置图片';
            currentImageData = imageData;
            break;
        case 'url':
            switchTab('url');
            imageUrlInput.value = imageData.url;
            urlPreview.style.display = 'block';
            urlPreviewImg.src = imageData.preview;
            urlStatus.textContent = '✓ URL已加载';
            currentImageData = imageData;
            break;
    }
}

// Tab切换
tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        switchTab(tab);
    });
});

function switchTab(tab) {
    // 更新按钮状态
    tabBtns.forEach(btn => {
        if (btn.dataset.tab === tab) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // 更新内容显示
    uploadTab.classList.remove('active');
    clipboardTab.classList.remove('active');
    urlTab.classList.remove('active');

    if (tab === 'upload') uploadTab.classList.add('active');
    else if (tab === 'clipboard') clipboardTab.classList.add('active');
    else if (tab === 'url') urlTab.classList.add('active');
}

// 上传图片
selectFileBtn.addEventListener('click', () => {
    imageFileInput.click();
});

imageFileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
        showModalStatus('请选择图片文件', 'error');
        return;
    }

    // 预览图片
    const reader = new FileReader();
    reader.onload = (e) => {
        uploadPreviewImg.src = e.target.result;
        uploadFileName.textContent = file.name;
        uploadPreview.style.display = 'block';

        currentImageData = {
            type: 'upload',
            file: file,
            preview: e.target.result,
            filename: file.name
        };
    };
    reader.readAsDataURL(file);
});

// 剪贴板粘贴
pasteZone.setAttribute('tabindex', '0');

pasteZone.addEventListener('click', () => {
    pasteZone.focus();
});

pasteZone.addEventListener('focus', () => {
    pasteZone.classList.add('active');
});

pasteZone.addEventListener('blur', () => {
    pasteZone.classList.remove('active');
});

pasteZone.addEventListener('paste', async (e) => {
    e.preventDefault();

    const items = e.clipboardData.items;
    let imageFile = null;

    for (let item of items) {
        if (item.type.startsWith('image/')) {
            imageFile = item.getAsFile();
            break;
        }
    }

    if (imageFile) {
        const reader = new FileReader();
        reader.onload = (e) => {
            clipboardPreviewImg.src = e.target.result;
            clipboardPreview.style.display = 'block';

            currentImageData = {
                type: 'clipboard',
                file: imageFile,
                preview: e.target.result,
                filename: `clipboard_${Date.now()}.png`
            };

            showModalStatus('✓ 图片粘贴成功！', 'success');
        };
        reader.readAsDataURL(imageFile);
    } else {
        showModalStatus('剪贴板中没有图片', 'error');
    }
});

// URL图片
loadUrlBtn.addEventListener('click', () => {
    const url = imageUrlInput.value.trim();
    if (!url) {
        showModalStatus('请输入图片URL', 'error');
        return;
    }

    // 验证URL格式
    try {
        new URL(url);
    } catch {
        showModalStatus('URL格式不正确', 'error');
        return;
    }

    // 尝试加载图片
    const img = new Image();
    img.crossOrigin = 'anonymous';

    img.onload = () => {
        urlPreviewImg.src = url;
        urlPreview.style.display = 'block';
        urlStatus.textContent = '✓ 图片加载成功';
        urlStatus.style.color = '#28a745';

        currentImageData = {
            type: 'url',
            url: url,
            preview: url
        };

        showModalStatus('✓ URL图片加载成功', 'success');
    };

    img.onerror = () => {
        urlPreview.style.display = 'none';
        urlStatus.textContent = '✗ 图片加载失败，请检查URL';
        urlStatus.style.color = '#dc3545';
        showModalStatus('图片加载失败，请检查URL是否正确', 'error');
    };

    img.src = url;
});

// 显示模态框状态消息
function showModalStatus(message, type) {
    modalStatus.textContent = message;
    modalStatus.className = 'modal-status ' + type;
    modalStatus.style.display = 'block';

    setTimeout(() => {
        modalStatus.style.display = 'none';
    }, 3000);
}

// 保存图片设置
saveImageBtn.addEventListener('click', async () => {
    if (!currentImageData) {
        showModalStatus('请先选择或上传图片', 'error');
        return;
    }

    // 如果是文件上传或剪贴板，先上传到服务器
    if (currentImageData.type === 'upload' || currentImageData.type === 'clipboard') {
        saveImageBtn.disabled = true;
        saveImageBtn.textContent = '上传中...';

        const formData = new FormData();
        formData.append('image', currentImageData.file);

        try {
            const response = await fetch('/api/upload-image', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                currentImageData.uploadedPath = data.path;
                currentImageData.filename = data.filename;

                // 保存到 topicImages
                topicImages.set(currentTopicIndex, currentImageData);

                // 更新按钮状态
                updateImageButtonStatus(currentTopicIndex, true);

                showModalStatus('✓ 图片设置成功！', 'success');
                setTimeout(() => {
                    closeImageModal();
                }, 1000);
            } else {
                const error = await response.json();
                showModalStatus('上传失败: ' + error.error, 'error');
            }
        } catch (error) {
            showModalStatus('上传失败，请重试', 'error');
        } finally {
            saveImageBtn.disabled = false;
            saveImageBtn.textContent = '保存设置';
        }
    } else if (currentImageData.type === 'url') {
        // URL类型直接保存
        topicImages.set(currentTopicIndex, currentImageData);
        updateImageButtonStatus(currentTopicIndex, true);
        showModalStatus('✓ 图片设置成功！', 'success');
        setTimeout(() => {
            closeImageModal();
        }, 1000);
    }
});

// 清除图片设置
clearImageBtn.addEventListener('click', () => {
    if (currentTopicIndex !== null) {
        topicImages.delete(currentTopicIndex);
        updateImageButtonStatus(currentTopicIndex, false);
    }
    closeImageModal();
});

// 取消
cancelImageBtn.addEventListener('click', closeImageModal);
modalClose.addEventListener('click', closeImageModal);

// 点击模态框外部关闭
imageModal.addEventListener('click', (e) => {
    if (e.target === imageModal) {
        closeImageModal();
    }
});

// 更新图片按钮状态
function updateImageButtonStatus(topicIndex, hasImage) {
    const wrapper = document.querySelector(`.topic-input-wrapper[data-index="${topicIndex}"]`);
    if (!wrapper) return;

    const imageBtn = wrapper.querySelector('.image-set-btn');
    if (!imageBtn) return;

    if (hasImage) {
        imageBtn.classList.add('has-image');
        imageBtn.innerHTML = '🖼️ 已设置 <span class="image-indicator"></span>';
    } else {
        imageBtn.classList.remove('has-image');
        imageBtn.textContent = '🖼️ 图片设置';
    }
}
